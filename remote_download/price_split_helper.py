# -*- coding: utf-8 -*-
import pandas as pd
import time
import os
import re
from config.configuration import get_sale_price, init_files_manager, price_special_case_manager, filter_price_data


class PriceSplitHelper:
    def __init__(self):
        self.default_value = False
        self.site_to_store_dict = {"BK": "BL", "WL": "WL", "TS": "TS"}
        self.date_str = time.strftime("%Y%m%d", time.localtime())
        self.root_path = os.path.dirname(__file__)
        self.price_save_name = None
        self.local_price_dir = None

    def _filter_merge_files(self, shop_name_abbr):
        files_manager = init_files_manager(self.root_path, shop_name_abbr, self.date_str)
        local_dir = files_manager.get("DownloadFilesDir")
        self.local_price_dir = files_manager.get("PriceFilesDir")
        self.price_save_name = files_manager.get("PriceSave")
        price_columns = files_manager.get("PriceColumns")
        reference_columns = files_manager.get("ReferenceColumns")
        mix_price_list = pd.DataFrame(columns=price_columns)
        mix_reference_list = pd.DataFrame(columns=reference_columns)
        price_filter = "{}_{}_{}.csv".format(shop_name_abbr, "price", self.date_str).lower()

        reference_filter = "{}_{}_{}.csv".format(shop_name_abbr, "reference", self.date_str).lower()

        if os.path.exists(local_dir):
            all_files = os.listdir(local_dir)
            files = []
            for f in all_files:
                if re.search(r"{}".format(self.date_str), f):
                    files.append(f)
            price_data_list = []
            reference_data_list = []
            for f in files:
                # if re.search(r"price", f):
                #     price_file = os.path.join(local_dir, f)
                #     price_data = pd.read_csv(price_file, delimiter="\t")
                #     price_data_list.append(price_data)
                #     # os.remove(price_file)
                # elif re.search(r"reference", f):
                #     reference_file = os.path.join(local_dir, f)
                #     reference_data = pd.read_csv(reference_file, delimiter="\t")
                #     reference_data_list.append(reference_data)
                #     # os.remove(reference_file)
                # else:
                #     pass

                if f == price_filter:
                    price_file = os.path.join(local_dir, f)
                    price_data = pd.read_csv(price_file, delimiter="\t")
                    price_data_list.append(price_data)
                    os.remove(price_file)
                elif f == reference_filter:
                    reference_file = os.path.join(local_dir, f)
                    reference_data = pd.read_csv(reference_file, delimiter="\t")
                    reference_data_list.append(reference_data)
                    os.remove(reference_file)
                else:
                    pass

            for price_data in price_data_list:
                if mix_price_list.empty:
                    mix_price_list = price_data
                else:
                    mix_price_list = pd.merge(mix_price_list, price_data, how="outer")

            for reference_data in reference_data_list:
                if mix_reference_list.empty:
                    mix_reference_list = reference_data
                else:
                    mix_reference_list = pd.merge(mix_reference_list, reference_data, how="outer")

            # mix_price_list.columns = price_columns
            # mix_reference_list.columns = reference_columns
            return mix_price_list, mix_reference_list

        else:
            return mix_price_list, mix_reference_list

    def split_price(self, shop_name_abbr, gap_price=2, compare=">", plus_limit=None, minus_limit=-8, query_code=None):
        # price columns = ["id","site","isbn", "product_id","variant_id","sku","basic_price","price_note","crawl_time"]
        # reference columns = ["product_id", "variant_id", "sku", "condition_isbn", "old_price", "quantity", "filter"]
        price_list, reference = self._filter_merge_files(shop_name_abbr)
        price_list[["product_id", "variant_id"]] = price_list[["product_id", "variant_id"]].astype(str)
        reference[["product_id", "variant_id"]] = reference[["product_id", "variant_id"]].astype(str)
        store_grouped = price_list.groupby(by="site")
        price_list_num = price_list.shape[0]
        reference_num = reference.shape[0]
        print("Price / Reference :  {} / {}".format(price_list_num, reference_num))
        mix_price_list = pd.DataFrame()
        for site, price_info in store_grouped:
            if not self.site_to_store_dict or not self.site_to_store_dict.get(site):
                store_name = site
            else:
                store_name = self.site_to_store_dict.get(site)

            if store_name == shop_name_abbr:

                price_detail = price_info.loc[:, ["product_id", "variant_id", "basic_price"]]

                # no price info
                zero_price = price_detail[price_detail.loc[:, 'basic_price'] == 0]
                null_price = price_detail.loc[price_detail['basic_price'].isnull(), :]
                null_zero_list = pd.merge(zero_price, null_price, how="outer")

                # normal price data
                price_detail = price_detail.dropna(subset=['basic_price'])
                price_detail.loc[:, 'new_price'] = pd.Series((get_sale_price(store_name, x)
                                                              for x in price_detail['basic_price']), index=price_detail.index)

                # old price info
                reference_price = reference.loc[:, ["product_id", "variant_id", "old_price", "quantity"]]
                merged_null_zero_price = pd.merge(null_zero_list, reference_price, how="left", on=["product_id", "variant_id"])
                merged_price_detail = pd.merge(price_detail, reference_price, how="left",
                                               on=["product_id", "variant_id"])                

                # deal with old price missing data - no inventory info
                merged_null_zero_price = price_special_case_manager(merged_null_zero_price, "OldPriceMissing")
                init_size = merged_null_zero_price.shape[0]
                merged_price_detail = price_special_case_manager(merged_price_detail, "OldPriceMissing", init_size)

                # filter null zero data to decrease update number by quantity
                merged_null_zero_price = merged_null_zero_price[merged_null_zero_price["quantity"] > 0]

                # deal normal price data---create "gas_price" to filter and reset columns
                merged_price_detail.loc[:, "gap_price"] = merged_price_detail["new_price"] - merged_price_detail["old_price"]
                export_null_price = merged_null_zero_price.loc[:, ["product_id", "variant_id", "basic_price", "old_price"]]
                export_null_price.rename(columns={'old_price': 'sort_value'}, inplace=True)
                export_price_detail = merged_price_detail.loc[:, ["product_id", "variant_id", "basic_price", "gap_price", "quantity"]]

                # filter and split normal data to get "filtered price data" & "out-of-filter price data-minus gap price"
                export_price_detail, minus_gap_price_list = filter_price_data(export_price_detail, gap_price, compare,
                                                                              plus_limit, minus_limit, query_code)
                if not minus_gap_price_list.empty:
                    # merge price data to satisfy max-update-number
                    merged_data = (export_price_detail, minus_gap_price_list)
                    init_size = export_price_detail.shape[0] + export_null_price.shape[0]
                    case = "AddMinusPrice"
                    export_price_detail = price_special_case_manager(merged_data, case, init_size)

                export_price_detail.rename(columns={'gap_price': 'sort_value'}, inplace=True)
                if not os.path.exists(self.local_price_dir):
                    os.makedirs(self.local_price_dir)
                mix_price_list = pd.merge(export_null_price, export_price_detail, how="outer")
                mix_price_list = mix_price_list.drop_duplicates()
                save_file_path = os.path.join(self.local_price_dir, self.price_save_name)
                mix_price_list.to_csv(save_file_path, sep="\t", index=False)
                null_price_size = null_price.shape[0]
                zero_price_size = zero_price.shape[0]
                normal_price_size = merged_price_detail.shape[0]
                print("NULL/ZERO/NORMAL: {} / {} / {}".format(null_price_size, zero_price_size, normal_price_size))
                break
        return mix_price_list

