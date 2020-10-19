# -*- coding: utf-8 -*-
import shopify
import re
import time
import random
import pandas
import os

from shopify_lib.shopify_to_google_merchant import ShopifyToGoogleMerchant
from shopping.google_merchant_helper import GoogleMerchantHelper
from config.configuration import init_shopify_store_configuration, variant_merchant_check, \
    get_sale_price, split_price_by_value, init_files_manager


class ShopifyPriceUpdate:
    def __init__(self, shop_name_abbr=None):
        self.root_path = os.path.dirname(__file__)
        self.date_str = time.strftime("%Y%m%d", time.localtime())
        files_manager = init_files_manager(self.root_path, shop_name_abbr, self.date_str)
        self.log_file_dir = files_manager.get("LogFilesDir")
        self.log_save_name = files_manager.get("LogSave")
        if not os.path.exists(self.log_file_dir):
            os.makedirs(self.log_file_dir)
        shop_info = init_shopify_store_configuration(shop_name_abbr)
        self.shop_name_abbr = shop_info.get("shop_name_abbr")
        self.api_key = shop_info.get("api_key")
        self.password = shop_info.get("password")
        self.shop_name = shop_info.get("shop_name")

        # # API 4.4.0
        # self.shop_url = "https://%s:%s@%s.myshopify.com/admin" % (self.api_key, self.password, self.shop_name)
        # shopify.ShopifyResource.set_site(self.shop_url)

        # API 5.1.0
        self.shop_url = "https://%s.myshopify.com/admin" % self.shop_name
        shopify.ShopifyResource.set_user(self.api_key)
        shopify.ShopifyResource.set_password(self.password)
        shopify.ShopifyResource.set_site(self.shop_url)

        self.shop_to_merchant_helper = ShopifyToGoogleMerchant(self.shop_name_abbr)
        self.merchant_helper = GoogleMerchantHelper(self.shop_name_abbr)
        self.default_value = None

    def _init_update_log_record(self, group=None, start_id=None, id_index=None, size=None, note=None, update=False):
        if group or start_id or size:
            time_stamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            if not note:
                note = "Processing"
                if id_index == size:
                    note = "Done"
            data = [group, start_id, id_index, size, note, time_stamp]
        else:
            data = None
        log_record_file = os.path.join(self.log_file_dir, self.log_save_name)
        log_columns = ["group", "id", "index", "size", "note", "time"]
        if os.path.exists(log_record_file):
            log_data = pandas.read_csv(log_record_file, delimiter="\t")
        else:
            log_data = pandas.DataFrame(columns=log_columns)

        if not data:
            if log_data.empty:
                group_start = 0
                index_start = 0
            else:
                processing_log = log_data[log_data.loc[:, "note"] == "Processing"]
                if processing_log.empty:
                    processing_log = log_data[log_data.loc[:, "note"] == "Done"]

                index = processing_log.shape[0] - 1
                group_start = processing_log.iloc[index]['group']
                index_start = processing_log.iloc[index]['index']

                log_size = log_data.shape[0]
                last_group_start = log_data["group"].tolist()[-1]
                last_id_start = log_data["id"].tolist()[-1]
                if log_size >= 2:
                    up_group_start = log_data["group"].tolist()[-2]
                    up_id_start = log_data["id"].tolist()[-2]
                    if up_group_start == last_group_start and up_id_start == last_id_start:
                        try:
                            index_start = int(index_start) + 1
                        except Exception as e:
                            print("Id Start Error- {}".format(e))
                            group_start = group_start + 1
                            index_start = 0
            return group_start, index_start
        else:
            if log_data.empty or not update:
                new_log = pandas.DataFrame([data], columns=log_columns)
                log_data = log_data.append(new_log)
                log_data.to_csv(log_record_file, sep="\t", index=False)

            else:
                index = log_data.shape[0] - 1
                log_data.iloc[index, :] = data
                log_data.to_csv(log_record_file, sep="\t", index=False)

    def _save_product_attribute(self, attribute_object):
        if self.default_value:
            pass

        attribute_id = attribute_object.attributes.get("id")
        try:
            success = attribute_object.save()
        except Exception as e:
            string = str(e)
            if re.search(r"Exceeded 2 calls per second for api client", string):
                print("Speed of saving operation is too fast")
                result = re.search(r"Retry-After': '(\d\.\d)", string)
                if not result:
                    sleep_time = 2.0
                else:
                    sleep_time = float(result.group(1))
                time.sleep(sleep_time + 1.0)

                try:
                    success = attribute_object.save()
                except Exception as e:
                    print("System error when saving {} : ".format(attribute_id), end=" ")
                    print(e)
                    return None
                else:
                    if success:
                        attribute_id = attribute_object.attributes.get("id")
                        return attribute_id
                    else:
                        print("Saving {} fails".format(attribute_id), end=' :')
                        print(attribute_object.errors.full_messages())
                        return None
            elif re.search(r"Daily variant creation limit reached", string):
                print("Daily variant creation limit reached.Please try again later-Save product error")
                return None
            else:
                print("System error when saving {} : ".format(attribute_id), end=" ")
                print(e)
                return None
        else:
            if success:
                attribute_id = attribute_object.attributes.get("id")
                return attribute_id
            else:
                print("Saving {} fails".format(attribute_id), end=' :')
                print(attribute_object.errors.full_messages())
                return None

    def _variant_price_update(self, variant_id, basic_price):
        new_sale_price = get_sale_price(self.shop_name_abbr, basic_price)
        if basic_price != basic_price:
            basic_price_show = False
        else:
            basic_price_show = basic_price
        if not new_sale_price:
            new_sale_price_show = False
        else:
            new_sale_price_show = new_sale_price
        try:
            variant = shopify.Variant.find(variant_id)
        except Exception as e:
            error_info = str(e)
            print(error_info)
            return None
        else:
            if new_sale_price:
                price_status = True
                new_compare_price = round(new_sale_price * 1.2 + random.uniform(1, 5), 2)
                old_sale_price = float(variant.price)
                if new_sale_price != old_sale_price:
                    variant.price = new_sale_price
                    variant.compare_at_price = new_compare_price
                    if not variant.inventory_quantity:
                        variant.inventory_quantity = 3
                    save_status = self._save_product_attribute(variant)
                else:
                    save_status = True
            else:
                price_status = False
                old_sale_price = float(variant.price)
                # variant.price = 0
                variant.inventory_quantity = 0
                save_status = self._save_product_attribute(variant)

            if save_status:
                product_id = variant.attributes["product_id"]
                record_data_list = [variant_id, product_id, basic_price_show, old_sale_price, new_sale_price_show,
                                    price_status]
                print("{}: {}".format(self.shop_name_abbr, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())),
                      end=" :")
                print(record_data_list)
                return record_data_list
            else:
                return None

    def _product_variant_price_update(self, product_id, variant_list):
        updated_variant_list = []
        for variant in variant_list:
            variant_id, basic_price = variant
            result = self._variant_price_update(variant_id, basic_price)
            if result:
                price_status = result[5]
                if price_status:
                    new_sale_price = result[4]
                else:
                    new_sale_price = result[3]
                result.append(False)
                updated_variant_list.append([variant_id, new_sale_price, price_status])

        if updated_variant_list:
            if variant_merchant_check(self.shop_name_abbr):
                merchant_info_list = []
                for variant_info in updated_variant_list:
                    updated_variant_id = variant_info[0]
                    new_sale_price = variant_info[1]
                    price_status = variant_info[2]
                    inventory_quantity = 3 if price_status else 0
                    merchant_info = self.shop_to_merchant_helper.format_merchant_inventory(product_id,
                                                                                           updated_variant_id,
                                                                                           new_sale_price,
                                                                                           inventory_quantity)
                    merchant_info_list.append(merchant_info)
                return merchant_info_list
            else:
                if len(updated_variant_list) == 2:
                    price1_status = updated_variant_list[0][2]
                    price2_status = updated_variant_list[1][2]
                    if price1_status and price2_status:
                        try:
                            price1 = float(updated_variant_list[0][1])
                            price2 = float(updated_variant_list[1][1])
                        except (ValueError, TypeError):
                            return None
                        else:
                            if price1 <= price2:
                                chosen_variant = updated_variant_list[0]
                            else:
                                chosen_variant = updated_variant_list[1]
                    else:
                        if not price1_status:
                            chosen_variant = updated_variant_list[1]
                        elif not price2_status:
                            chosen_variant = updated_variant_list[0]
                        else:
                            chosen_variant = updated_variant_list[0]
                    chosen_variant_id = chosen_variant[0]
                    new_sale_price = chosen_variant[1]
                    price_status = chosen_variant[2]
                    merchant_info = self.shop_to_merchant_helper.format_merchant_inventory(product_id,
                                                                                           chosen_variant_id,
                                                                                           new_sale_price,
                                                                                           price_status)
                    return merchant_info

                elif len(updated_variant_list) == 1:
                    merchant_info_list = self.shop_to_merchant_helper.retrieve_product_merchant_price_by_ids(product_id)
                    if merchant_info_list:
                        return merchant_info_list[0]
                    else:
                        return None
                else:
                    pass
        else:
            return None

    def _columns_index_check(self, columns, column_name1, column_name2, tip):
        if self.default_value:
            pass
        try:
            column_name_index = columns.index(column_name1)
        except ValueError:
            try:
                column_name_index = columns.index(column_name2)
            except ValueError:
                raise KeyError("CSV file head column format is illegal for {}".format(tip))
            else:
                return column_name_index
        else:
            return column_name_index

    def product_variant_price_update_by_pandas_data(self, price_data_info):
        # default columns = ["product_id", "variant_id", "basic_price", "sort_value"]
        product_price_data = price_data_info
        columns = list(product_price_data.columns)
        variant_id_index = self._columns_index_check(columns, "variant_id", "variantid", "variant id")
        price_index = self._columns_index_check(columns, "basic_price", "price", "basic price")
        product_id_index = self._columns_index_check(columns, "product_id", "productid", "product id")
        product_id_name = columns[product_id_index]
        variant_id_name = columns[variant_id_index]
        price_name = columns[price_index]
        product_price_data[product_id_name] = product_price_data[product_id_name].astype(str)
        product_price_data[variant_id_name] = product_price_data[variant_id_name].astype(str)
        groups = split_price_by_value(product_price_data, price_name)

        group_start, index_start = self._init_update_log_record()
        for group in groups:
            group_num, price_data = group
            print("group- {}  size- {}".format(group_num, price_data.shape[0]))
            if group_num >= group_start:
                if not price_data.empty:
                    if "sort_value" in columns:
                        price_data.sort_values("sort_value", inplace=True, ascending=False)
                    else:
                        price_data.sort_values(price_name, inplace=True, ascending=True)
                    product_id_list = price_data[product_id_name].unique().tolist()
                    price_data.set_index(product_id_name, drop=False, inplace=True)
                    merchant_info_list = []
                    size = len(product_id_list)
                    for product_id in product_id_list:
                        index = product_id_list.index(product_id)
                        try:
                            if index >= index_start:
                                print(product_id)
                                product = price_data.loc[product_id]
                                try:
                                    variant_list = product.values[:, [variant_id_index, price_index]]
                                except IndexError:
                                    variant_list = [product.values[[variant_id_index, price_index]]]
                                merchant_info = self._product_variant_price_update(product_id, variant_list)

                                if merchant_info:
                                    if isinstance(merchant_info, list):
                                        for info in merchant_info:
                                            merchant_info_list.append(info)
                                    else:
                                        merchant_info_list.append(merchant_info)
                                length = len(merchant_info_list)
                                if length and length >= 50:
                                    self.merchant_helper.product_update_price_batch(merchant_info_list)
                                    merchant_info_list = []
                                    self._init_update_log_record(group_num, product_id, index+1, size, update=True)
                        except Exception as e:
                            error_note = str(e)
                            self._init_update_log_record(group_num, product_id, index+1, size, error_note)
                            raise TypeError("Something Wrong")
                        else:
                            if index == size - 1 and merchant_info_list:
                                self.merchant_helper.product_update_price_batch(merchant_info_list)
                                self._init_update_log_record(group_num, product_id, size, size, update=True)
