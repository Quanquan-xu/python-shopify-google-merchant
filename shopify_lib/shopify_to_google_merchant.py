# -*- coding: utf-8 -*-
import pyisbn
import shopify
import re
import time
import random
from config.configuration import init_shopify_store_configuration, format_merchant_offer_id,variant_merchant_check


class ShopifyToGoogleMerchant:
    def __init__(self, shop_name_abbr=None):
        self.merchant_offer_id_prefix = "online:en:US:"
        shop_info = init_shopify_store_configuration(shop_name_abbr)
        self.shop_name_abbr = shop_info.get("shop_name_abbr")
        self.api_key = shop_info.get("api_key")
        self.password = shop_info.get("password")
        self.shop_name = shop_info.get("shop_name")
        self.brand = shop_info.get("brand")
        self.sku_prefix = shop_info.get("sku_prefix")
        self.sku_check = shop_info.get("sku_check")
        self.mpn_prefix = shop_info.get("mpn_prefix")
        self.link_prefix = shop_info.get("link_prefix")
        self.no_available_image_link = shop_info.get("no_available_image_link")
        # # API 4.4.0
        # self.shop_url = "https://%s:%s@%s.myshopify.com/admin" % (self.api_key, self.password, self.shop_name)
        # shopify.ShopifyResource.set_site(self.shop_url)

        # API 5.1.0
        self.shop_url = "https://%s.myshopify.com/admin" % self.shop_name
        shopify.ShopifyResource.set_user(self.api_key)
        shopify.ShopifyResource.set_password(self.password)
        shopify.ShopifyResource.set_site(self.shop_url)
        self.default_value = None

    def _find_products_by_page(self, limit, page):
        if self.default_value:
            pass

        try:
            products = shopify.Product.find(limit=limit, page=page)
        except Exception as e:
            print(" System error when finding products(limit={}, page={})--TRY AGAIN AFTER 2s : ".format(limit, page),
                  end=" ")
            print(e)
            products = None

        if not products:
            time.sleep(2)
            try:
                products = shopify.Product.find(limit=limit, page=page)
            except Exception as e:
                print(" System error when finding products(limit={}, page={}. )--RETURN NONE : ".format(limit, page),
                      end=" ")
                print(e)
                return []
            else:
                return products
        else:
            return products

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

    def _find_product(self, product_id):
        if self.default_value:
            pass
        try:
            product = shopify.Product().find(product_id)
        except Exception as e:
            print("Speed is too fast")
            string = str(e)
            if re.search(
                    r"Exceeded 2 calls per second for api client",
                    string):
                result = re.search(r"Retry-After': '(\d\.\d)", string)
                sleep_time = float(result.group(1))
                time.sleep(sleep_time + 1.0)
                try:
                    product = shopify.Product().find(product_id)
                except Exception as e:
                    print("product id({}) error : ".format(product_id), end=" ")
                    print(e)
                    return False
                else:
                    return product
            else:
                print("product id({}) error : ".format(product_id), end=" ")
                print(e)
                return False
        else:
            return product

    def _delete_products(self, product_id_info):
        product_id_list = product_id_info if isinstance(product_id_info, list) else [product_id_info]
        for product_id in product_id_list:
            product = self._find_product(product_id)
            if not product:
                return False
            else:
                product.destroy()
                return True

    def mpn_decryption(self, mpn):

        if self.default_value:
            pass

        if mpn[0] == "0":
            prefix = ""
        else:
            prefix = "978"
        en_isbn10 = mpn[3:]

        isbn = ''
        for index in range(len(en_isbn10)):
            if en_isbn10[index] in ["A", "B", "C", "D", "E", "F", "G"]:
                suffix = "X"
                isbn = isbn + suffix
            else:
                isbn = isbn + str(int(en_isbn10[index]) + 5)[-1]

        length = len(isbn)
        de_isbn = ''
        de_isbn = de_isbn + str(isbn[0])
        index = 1
        while index < length:
            i = index
            j = index + 1
            if j < length - 1:
                de_isbn = de_isbn + str(isbn[j])
                de_isbn = de_isbn + str(isbn[i])
            elif i < length - 1:
                de_isbn = de_isbn + str(isbn[i])
            else:
                break
            index = index + 2
        de_isbn = de_isbn + str(isbn[length - 1])
        if not prefix:
            isbn13 = pyisbn.convert(de_isbn)
        else:
            isbn13 = prefix + de_isbn
        return isbn13

    def isbn_encryption(self, isbn, condition=None):

        if self.default_value:
            pass

        prefix = ""
        if len(isbn) == 10:
            isbn10 = isbn
            prefix = prefix + '0'
        else:
            isbn10 = isbn[3:]
            prefix = prefix + '1'

        if condition:
            if isinstance(condition, str):
                if condition.upper() == "NEW":
                    prefix = prefix + '1'
                elif condition.upper() == "USED":
                    prefix = prefix + '0'
            else:
                prefix = prefix + ["0", '1'][random.randint(0, 1)]
        else:
            prefix = prefix + ["0", '1'][random.randint(0, 1)]

        random_num = random.randint(0, 9)
        prefix = prefix + str(random_num)

        isbn = ''
        for index in range(len(isbn10)):
            if isbn10[index] == "X":
                suffix_list = ["A", "B", "C", "D", "E", "F", "G"]
                temp_index = random.randint(0, 6)
                suffix = suffix_list[temp_index]
                isbn = isbn + suffix
            else:
                isbn = isbn + str(int(isbn10[index]) + 5)[-1]

        length = len(isbn)
        en_isbn = ''
        en_isbn = en_isbn + str(isbn[0])
        index = 1
        while index < length:
            i = index
            j = index + 1
            if j < length - 1:
                en_isbn = en_isbn + str(isbn[j])
                en_isbn = en_isbn + str(isbn[i])
            elif i < length - 1:
                en_isbn = en_isbn + str(isbn[i])
            else:
                break
            index = index + 2
        en_isbn = en_isbn + str(isbn[length - 1])
        return prefix + en_isbn

    def _format_product_title(self, new_title, author=None, binding=None, pubdate=None):
        if self.default_value:
            pass

        if "Paperback" in new_title.split("(")[-1] or "Hardcover" in new_title.split("(")[-1]:
            title = new_title
        else:
            if author:
                if len(author) > 50 or len(author.split(",")) >= 3:
                    authors = author.split(",")
                    if len(authors) >= 3:
                        author = authors[0:2]
                        author = ','.join(author) + ", etc."
                    else:
                        if len(authors) >= 2:
                            author = authors[0]
                            if len(author) > 50:
                                author = None
                            else:
                                author = author + ", etc."
                        else:
                            author = None
            if pubdate:
                pubdate_part = pubdate.split(" ")
                if len(pubdate_part) >= 3:
                    pub_date = ' '.join(pubdate_part[-3:])
                else:
                    pub_date = None
            else:
                pub_date = None

            if not binding:
                title = new_title.strip()
            else:
                if new_title.strip() and new_title[-1] == ")":
                    if author:
                        if pub_date and random.randint(0, 1) and len(new_title) <= 190:
                            title_suffix = "- {} {} {}".format(binding, pub_date, author)
                            if len(new_title + title_suffix) >= 255:
                                title_suffix = "- {} By {}".format(binding, author)
                        else:
                            title_suffix = "- {} By {}".format(binding, author)

                        if len(new_title + title_suffix) >= 255:
                            title_suffix = "- {}".format(binding)
                    else:
                        if pub_date and random.randint(0, 1):
                            title_suffix = "- {} {}".format(binding, pub_date)
                            if len(new_title + title_suffix) >= 255:
                                title_suffix = "- {}".format(binding)
                        else:
                            title_suffix = "- {}".format(binding)
                else:
                    if author:
                        if pub_date and random.randint(0, 1) and len(new_title) <= 190:
                            title_suffix = "({} - {} - {})".format(binding, pub_date, author)
                            if len(new_title + title_suffix) >= 255:
                                title_suffix = "({} By {})".format(binding, author)
                        else:
                            title_suffix = "({} By {})".format(binding, author)

                        if len(new_title + title_suffix) >= 255:
                            title_suffix = "({})".format(binding)
                    else:
                        if pub_date and random.randint(0, 1):
                            title_suffix = "({} - {})".format(binding, pub_date)
                            if len(new_title + title_suffix) >= 255:
                                title_suffix = "({})".format(binding)
                        else:
                            title_suffix = "({})".format(binding)

                if len(new_title + title_suffix) >= 255:
                    title = new_title
                else:
                    title = "{} {}".format(new_title, title_suffix) if new_title.strip() else ''
        return title

    def _modify_handle_sku(self, product):
        try:
            product_id = product.id
            print("#" * 30)
            print("Product id : {} ({})".format(product_id,
                                                time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))

            # modify product handle&title
            original_handle = product.handle
            handle_part = original_handle.split("-")
            if len(handle_part[0]) == 13:
                try:
                    int(handle_part[0])
                except ValueError:
                    new_handle = "-".join(handle_part)
                else:
                    if len(handle_part[1]) == 10:
                        try:
                            int(handle_part[1][:-1])
                        except ValueError:
                            new_handle = "-".join(handle_part[1:])
                        else:
                            new_handle = "-".join(handle_part[2:])
                    else:
                        new_handle = "-".join(handle_part[1:])
            elif len(handle_part[0]) == 10:
                try:
                    int(handle_part[0][:-1])
                except ValueError:
                    new_handle = "-".join(handle_part)
                else:
                    if len(handle_part[1]) == 13:
                        try:
                            int(handle_part[1])
                        except ValueError:
                            new_handle = "-".join(handle_part[1:])
                        else:
                            new_handle = "-".join(handle_part[2:])
                    else:
                        new_handle = "-".join(handle_part[1:])
            else:
                new_handle = "-".join(handle_part)

            original_title = product.title
            if not original_title:
                original_title = ' '
            if original_title[0] == "\"" and original_title[-1] == "\"":
                new_title = original_title[1:-1].replace("\"\"", "\"")
                new_title = new_title.replace("\"\"", "\"")
            else:
                new_title = original_title.replace("\"\"", "\"")

            if "Paperback" in new_title.split("(")[-1] or "Hardcover" in new_title.split("(")[-1]:
                title = new_title
            else:
                meta_fields = product.metafields()
                meta_field_values = {}
                for meta_field in meta_fields:
                    meta_field_values[meta_field.attributes['key']] = meta_field.attributes["value"]
                author = meta_field_values.get("author")
                binding = meta_field_values.get("binding")
                pubdate = meta_field_values.get("pubdate")
                title = self._format_product_title(new_title, author, binding, pubdate)

            product.title = title
            product.handle = new_handle
            save_status = self._save_product_attribute(product)
            if save_status:
                try:
                    print(title)
                except UnicodeEncodeError:
                    print("Title includes UnicodeEncodeError")
            else:
                print("Something wrong with product title& handle saving (product id :{})".format(product_id))

            # modify variants
            variants = product.attributes["variants"]
            isbn13_status = 0
            for variant in variants:
                variant_id = variant.attributes.get("id")
                sku = variant.attributes.get('sku')
                barcode = variant.attributes.get("barcode")
                variant_title = variant.attributes.get("title")

                if len(barcode) <= 10:
                    isbn13 = pyisbn.convert(barcode)
                    isbn10 = pyisbn.convert(isbn13)
                else:
                    isbn10 = pyisbn.convert(barcode)
                    isbn13 = pyisbn.convert(isbn10)
                if variant_title[0] == "U":
                    condition = 'used'
                else:
                    condition = "new"

                isbn = [isbn10, isbn13][random.randint(0, 1)]
                mpn = self.isbn_encryption(isbn, condition)

                new_variant = shopify.Variant.find(variant_id)
                sku_part = sku.split("-", 3)
                sku_part[-1] = mpn
                new_sku = '-'.join(sku_part)
                new_variant.sku = new_sku
                print(new_variant.sku)
                save_status = self._save_product_attribute(new_variant)
                if save_status:
                    isbn_de = self.mpn_decryption(mpn)
                    if isbn_de == isbn13:
                        isbn13_status += 1
                else:
                    print("Something wrong with variant saving or mpn encryption (product id :{})".format(product_id))
            if isbn13_status != 2:
                raise TypeError("Something wrong with mpn encryption or saving (product id :{})".format(product_id))
        except Exception as e:
            error_info = str(e)
            print(error_info, end=" ")
            print("$#@" * 20)
            return None
        else:
            modified_product = shopify.Product.find(product_id)
            return modified_product

    def _sku_status_check(self, variant):
        if self.sku_check:
            sku = variant.attributes.get('sku')
            sku_element_list = sku.split("-")
            if sku_element_list[0] == self.sku_prefix:
                if sku_element_list[-1][0] in ["U", "N"]:
                    return 0
                elif sku_element_list[-1][0] in ["0", "1"]:
                    return 1
                else:
                    return False
            else:
                return -1
        else:
            return 1

    def _extract_merchant_variant(self, variants):
        if self.default_value:
            pass
        try:
            price1 = float(variants[0].attributes.get("price"))
            price2 = float(variants[1].attributes.get("price"))
        except ValueError:
            return None
        else:
            if price2 and price1 > price2:
                return variants[1]
            else:
                if price1:
                    return variants[0]
                else:
                    if price2:
                        return variants[1]
                    else:
                        return None

    def _extract_product_merchant_info(self, product, variant_id=None):
        product_id = product.id
        variants = product.attributes["variants"]

        for variant in variants:
            if not self._sku_status_check(variant):
                product = self._modify_handle_sku(product)
        if product:
            product_id = product.id
            title = product.attributes["title"]
            ascii_title = (title.encode('ascii', 'ignore')).decode("utf-8")
            description = product.attributes["body_html"]
            if not description:
                description = ascii_title
            ascii_description = (description.encode('ascii', 'ignore')).decode("utf-8")
            handle = product.attributes["handle"]

            vendor = product.attributes["vendor"]
            product_type = product.attributes["product_type"]
            tags = product.attributes["tags"]

            images = product.attributes["images"]
            image_list = []
            for image in images:
                image_list.append(image.attributes.get("src"))

            if not variant_id:
                variants = product.attributes["variants"]
                if len(variants) == 2 and self._sku_status_check(variants[0]) == 1:
                    variant = self._extract_merchant_variant(variants)
                else:
                    print("Product has not only two variants")
                    variant = None
            else:
                try:
                    variant = shopify.Variant.find(variant_id)
                except Exception as e:
                    error_string = str(e)
                    print(error_string)
                    variant = None
            if variant:
                variant_id = variant.attributes.get("id")
                price = variant.attributes.get("price")
                sku = variant.attributes.get('sku')
                weight = variant.attributes.get("grams")
                barcode = variant.attributes.get("barcode")
                if variant_merchant_check(self.shop_name_abbr):
                    quantity = int(variant.attributes.get("inventory_quantity"))
                    title = variant.attributes.get("title")
                    temp_condition = title.split("/")[-1].lower()
                    if temp_condition in ["new", "used"]:
                        condition = temp_condition
                    else:
                        condition = "new"
                else:
                    quantity = 3
                    condition = "new"
                try:
                    if len(barcode) <= 10:
                        isbn13 = pyisbn.convert(barcode)
                        isbn10 = pyisbn.convert(isbn13)
                    else:
                        isbn10 = pyisbn.convert(barcode)
                        isbn13 = pyisbn.convert(isbn10)
                except pyisbn.IsbnError:
                    isbn10 = barcode
                    isbn13 = None
                if quantity > 0:
                    availability = 'in stock'
                else:
                    availability = 'out of stock'

                try:
                    weight_lb = "%.2f" % (int(weight) * 0.00220462262185)
                except ValueError:
                    weight_lb = variant.attributes.get("weight")
                    print("weight error")
                link = handle + "?variant=" + str(variant_id)
                mpn = self._format_mpn(sku, isbn13)
                offer_id = format_merchant_offer_id(self.shop_name_abbr, product_id, variant_id)
                details = {
                    "product_id": offer_id,
                    "sku": sku,
                    "mpn": mpn,
                    "isbn13": isbn13,
                    "isbn10": isbn10,
                    "price": price,
                    "condition": condition,
                    "availability": availability,
                    "title": ascii_title,
                    "description": ascii_description,
                    "images": ';'.join(image_list),
                    "quantity": quantity,
                    "weight": weight,
                    "weight_lb": weight_lb,
                    "link": self.link_prefix + link,
                    "vendor": vendor,
                    "product_type": product_type,
                    "tags": tags,
                    "brand": self.brand
                }
                return details
            else:
                print("No available variant")
                return None
        else:
            print("Modify product({}) false".format(product_id))
            return None
   
    def _extract_product_variants_merchant_info(self, product):
        merchant_info_list = []
        product_id = product.id
        title = product.attributes["title"]
        ascii_title = (title.encode('ascii', 'ignore')).decode("utf-8")
        description = product.attributes["body_html"]
        if not description:
            description = ascii_title
        ascii_description = (description.encode('ascii', 'ignore')).decode("utf-8")
        handle = product.attributes["handle"]

        vendor = product.attributes["vendor"]
        product_type = product.attributes["product_type"]
        tags = product.attributes["tags"]

        images = product.attributes["images"]
        image_list = []
        for image in images:
            image_list.append(image.attributes.get("src"))
        variants = product.attributes["variants"]
        for variant in variants:
            variant_id = variant.attributes.get("id")
            price = variant.attributes.get("price")
            sku = variant.attributes.get('sku')
            weight = variant.attributes.get("grams")
            barcode = variant.attributes.get("barcode")

            quantity = int(variant.attributes.get("inventory_quantity"))
            format_title = variant.attributes.get("title")
            temp_condition = format_title.split("/")[-1].lower()
            if temp_condition.strip() in ["new", "used"]:
                condition = temp_condition.strip()
            else:
                condition = "new"
            try:
                if len(barcode) <= 10:
                    isbn13 = pyisbn.convert(barcode)
                    isbn10 = pyisbn.convert(isbn13)
                else:
                    isbn10 = pyisbn.convert(barcode)
                    isbn13 = pyisbn.convert(isbn10)
            except pyisbn.IsbnError:
                isbn10 = barcode
                isbn13 = None

            if quantity > 0:
                availability = 'in stock'
            else:
                availability = 'out of stock'

            try:
                weight_lb = "%.2f" % (int(weight) * 0.00220462262185)
            except ValueError:
                weight_lb = variant.attributes.get("weight")
                print("weight error")
            link = handle + "?variant=" + str(variant_id)

            mpn = self._format_mpn(sku, isbn13)
            offer_id = format_merchant_offer_id(self.shop_name_abbr, product_id, variant_id)
            details = {
                "product_id": offer_id,
                "sku": sku,
                "mpn": mpn,
                "isbn13": isbn13,
                "isbn10": isbn10,
                "price": price,
                "condition": condition,
                "availability": availability,
                "title": "{} ({})".format(ascii_title, format_title),
                "description": ascii_description,
                "images": ';'.join(image_list),
                "quantity": quantity,
                "weight": weight,
                "weight_lb": weight_lb,
                "link": self.link_prefix + link,
                "vendor": vendor,
                "product_type": product_type,
                "tags": tags,
                "brand": self.brand
            }
            merchant_info_list.append(details)
        return merchant_info_list

    def _retrieve_product_merchant_price(self, product, variant_id=None):
        if not variant_id:
            variants = product.attributes["variants"]
            if len(variants) == 2 and self._sku_status_check(variants[0]) == 1:
                variant = self._extract_merchant_variant(variants)
            else:
                print("Product has not only two variants")
                variant = None
        else:
            try:
                variant = shopify.Variant.find(variant_id)
            except Exception as e:
                error_string = str(e)
                print(error_string)
                variant = None
        if variant:
            variant_id = variant.attributes.get("id")
            price = variant.attributes.get("price")
            inventory_quantity = variant.attributes.get("inventory_quantity")
            return variant_id, price, inventory_quantity
        else:
            return None, None, None

    def _format_mpn(self, sku, isbn13):
        sku_part = sku.split("-")
        if self.sku_check:
            sku_part = sku.split("-")
            if len(sku_part) == 3:
                temp_mpn = sku.split("-")[-1]
                if self.mpn_decryption(temp_mpn) == isbn13:
                    mpn = self.mpn_prefix + temp_mpn
                else:
                    mpn = sku
            elif len(sku_part) == 1:
                mpn = sku
            else:
                mpn = sku_part[-1]
        else:
            if len(sku_part) == 3:
                temp_mpn = sku.split("-")[-1]
                mpn = self.mpn_prefix + temp_mpn
            elif len(sku_part) == 1:
                mpn = sku
            else:
                mpn =self.mpn_prefix + sku_part[-1]
        return mpn

    def format_merchant_inventory(self, product_id, variant_id, price, inventory_quantity=3):
        offer_id = format_merchant_offer_id(self.shop_name_abbr, product_id, variant_id)
        merchant_product_id = self.merchant_offer_id_prefix + offer_id
        inventory = {
            'availability': 'in stock' if inventory_quantity else 'out of stock',
            'price': {
                'value': float(price),
                'currency': 'USD'
            }
        }
        merchant_info = {"productId": merchant_product_id, "inventory": inventory,
                         "product_id": product_id, "variant_id": variant_id}
        return merchant_info

    def retrieve_product_merchant_price_by_ids(self, product_id_list, variant_id_list=None):
        product_id_list = product_id_list if isinstance(product_id_list, list) else [product_id_list]
        merchant_info_list = []
        for index in range(0, len(product_id_list)):
            product_id = product_id_list[index]
            product = self._find_product(product_id)
            variant_id = None
            if variant_id_list:
                variant_id = variant_id_list[index]
            if product:
                variant_id, price, inventory_quantity = self._retrieve_product_merchant_price(product, variant_id)
                if price:
                    merchant_info = self.format_merchant_inventory(product_id, variant_id, price, inventory_quantity)
                    merchant_info_list.append(merchant_info)
        return merchant_info_list

    def retrieve_product_merchant_info_by_ids(self, product_id_list, variant_id_list=None):
        product_id_list = product_id_list if isinstance(product_id_list, list) else [product_id_list]
        merchant_info_list = []
        for index in range(0, len(product_id_list)):
            product_id = product_id_list[index]
            product = self._find_product(product_id)
            variant_id = None
            if variant_id_list:
                variant_id = variant_id_list[index]
            if product:
                try:
                    result = self._extract_product_merchant_info(product, variant_id)
                except(AttributeError, ValueError, TypeError):
                    result = None
                if result:
                    merchant_info_list.append(result)
        return merchant_info_list

    def retrieve_product_merchant_info_by_page(self, page, limit=250):
        products = self._find_products_by_page(limit=limit, page=page)
        merchant_info_list = []
        for product in products:
            result = self._extract_product_merchant_info(product)
            if result:
                merchant_info_list.append(result)
        return merchant_info_list

    def retrieve_product_variants_merchant_info_by_page(self, page, limit=250):
        products = self._find_products_by_page(limit=limit, page=page)
        merchant_info_list = []
        for product in products:
            results = self._extract_product_variants_merchant_info(product)
            if results:
                for result in results:
                    merchant_info_list.append(result)
        return merchant_info_list

    def modify_product_images_by_id(self, product_id):
        print(product_id)
        product = self._find_product(product_id)
        if product:
            image_list = []
            image_url_list = [self.no_available_image_link]
            for image_url in image_url_list:
                image_list.append(shopify.Image(
                    {"src": image_url}
                ))
            product.images = image_list
            save_status = self._save_product_attribute(product)
            if save_status:
                print("Modify product images successfully")
                product = self._find_product(product_id)
                images = product.attributes["images"]
                image_list = []
                for image in images:
                    image_list.append(image.attributes.get("src"))
                return image_list
            else:
                print("Fail to modify product images")
                return None
        else:
            return None




