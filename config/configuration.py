# -*- coding: utf-8 -*-
import time
import os
import pandas as pd


def init_shopify_store_configuration(shop_name_abbr=None):

    if shop_name_abbr == 'BL':
        shop_name_abbr = 'BL'
        api_key = '6552e9a78ad27b4779ebde7271d24506'
        password = '164a12faf63807cc2ae270a07d669929'
        shop_name = 'bookloves'
        brand = "BookLoves"
        sku_prefix = "BK"
        sku_check = True
        mpn_prefix = "BL"
        link_prefix = "https://www.bookloves.com/products/"
        no_available_image_link = "https://cdn.shopify.com/s/files/1/0087/0976/7228/" \
                                  "products/bookloves_no_available_image_1024x1024.jpg"

    elif shop_name_abbr == 'WL':
        shop_name_abbr = 'WL'
        api_key = '621acc4d92916debe380450993380458'
        password = '98f864f9cf7d4806b9c30390b1f5d082'
        shop_name = 'the-book-we-love'
        brand = "BookWeLove"
        sku_prefix = "WL"
        sku_check = True
        mpn_prefix = "WL"
        link_prefix = "https://www.thebookwelove.com/products/"
        no_available_image_link = None

    elif shop_name_abbr == 'ST':
        shop_name_abbr = 'ST'
        api_key = 'b6144d1dd6c3164b6137511a136c4775'
        password = '04b673a191d7c0ea3be62c437c0eb9e9'
        shop_name = 'stevens-books-christian-today'
        brand = "StevensBooks"
        sku_prefix = ""
        sku_check = False
        mpn_prefix = ""
        link_prefix = "https://www.stevensbooks.com/products/"
        no_available_image_link = "https://cdn.shopify.com/s/files/1/1840/0701/" \
                                  "products/stevensbooks_no_available_image_large.jpg"
    elif shop_name_abbr == 'TS':
        shop_name_abbr = 'TS'
        api_key = 'dd68289d503e309ef4834cb36be4ce79'
        password = '737b232afd2aa7adfa5870aa77bf8106'
        shop_name = 'topsellerbook'
        brand = "TopSellerBook"
        sku_prefix = "TS"
        sku_check = True
        mpn_prefix = "TS"
        link_prefix = "https://topsellerbook.com/products/"
        no_available_image_link = None

    elif shop_name_abbr == 'OL':
        shop_name_abbr = 'OL'
        api_key = "cc504b75a8f178f9ab63ff7e82e8e1d3"
        password = "aafc9cfef16451450745b16c747dd54a"
        shop_name = "olivers-store-com"
        brand = "OliverStore"
        sku_prefix = "OL"
        sku_check = True
        mpn_prefix = "OL"
        link_prefix = "https://www.oliversstore.com/products/"
        no_available_image_link = None

    elif shop_name_abbr == 'CA':
        shop_name_abbr = 'CA'
        api_key = '27449ab76681686ea6ba68c01927bc67'
        password = '971f41e257b65738c867b6b899415b51'
        shop_name = 'collectiblealbum'
        brand = "Collectible Album"
        product_type = "CD"
        sku_prefix = "CA"
        sku_check = False
        mpn_prefix = "CA"
        link_prefix = "https://www.collectiblealbum.com/products/"
        no_available_image_link = None
    else:
        shop_name_abbr = 'BL'
        api_key = '6552e9a78ad27b4779ebde7271d24506'
        password = '164a12faf63807cc2ae270a07d669929'
        shop_name = 'bookloves'
        brand = "BookLoves"
        sku_prefix = "BK"
        sku_check = True
        mpn_prefix = "BL"
        link_prefix = "https://www.bookloves.com/products/"
        no_available_image_link = "https://cdn.shopify.com/s/files/1/0087/0976/7228/" \
                                  "products/bookloves_no_available_image_1024x1024.jpg"

    store_info = {
        "shop_name_abbr": shop_name_abbr,
        "api_key": api_key,
        "password": password,
        "shop_name": shop_name,
        "brand": brand,
        "sku_prefix": sku_prefix,
        "sku_check": sku_check,
        "mpn_prefix": mpn_prefix,
        "link_prefix": link_prefix,
        "no_available_image_link": no_available_image_link
    }
    return store_info


def init_google_merchant_configuration():
    pass


def format_merchant_offer_id(shop_name_abbr, product_id, variant_id):
    if shop_name_abbr in ["ST"]:
        offer_id = "shopify_{}_{}".format(product_id, variant_id)
    else:
        offer_id = str(product_id)
    return offer_id


def variant_merchant_check(shop_name_abbr):
    if shop_name_abbr in ["ST"]:
        return True
    else:
        return False


def free_shipping_check(shop_name_abbr):
    if shop_name_abbr in ["ST"]:
        return True
    else:
        return False


def get_sale_price(shop_name_abbr, basic_price):
    if basic_price != basic_price:
        sale_price = None
    else:
        try:
            basic_price = float(basic_price)
        except ValueError:
            basic_price = None
        except TypeError:
            basic_price = None

        if basic_price:
            if shop_name_abbr in ["ST", "TS", "OL"]:
                price1 = 1.6 * basic_price
                price2 = basic_price + 14.0
                sale_price = round(max(price1, price2), 2)

            else:
                price1 = 1.5 * basic_price
                price2 = basic_price + 12.0
                sale_price = round(max(price1, price2), 2)
        else:
            sale_price = basic_price
    return sale_price


def filter_price_data(mix_price_detail, gap_price=2, compare=">", plus_limit=None, minus_limit=-8, query_code=None):
    minus_gap_price_list = pd.DataFrame(columns=["product_id", "variant_id", "basic_price", "gap_price"])

    if query_code:
        price_update_list = mix_price_detail.query(query_code)
    else:
        if plus_limit:
            mix_price_detail = mix_price_detail[mix_price_detail["basic_price"] <= plus_limit]

        if compare == "<":
            price_update_list = mix_price_detail[mix_price_detail["gap_price"] < gap_price]
        elif compare == "==":
            price_update_list = mix_price_detail[mix_price_detail["gap_price"] == gap_price]
        else:
            price_update_list = mix_price_detail[mix_price_detail["gap_price"] > gap_price]
            minus_gap_price_list = mix_price_detail[mix_price_detail["gap_price"] < minus_limit]
            query_command = 'basic_price > 0 and {} <= gap_price <= {} and quantity == 0'.format(minus_limit, gap_price)
            abnormal_price_list = mix_price_detail.query(query_command)
            abnormal_price_list.loc[:, 'gap_price'] = 0
            price_update_list = price_update_list.append(abnormal_price_list)
    return price_update_list, minus_gap_price_list


def split_price_by_value(price_data, filter_name):
    columns = price_data.columns

    if "sort_value" in columns:
        plus_price_data = price_data[price_data["sort_value"] > 0]
        minus_price_data = price_data[price_data["sort_value"] < 0]
    else:
        plus_price_data = price_data
        minus_price_data = pd.DataFrame(columns=columns)
    abnormal_inventory = price_data.query("sort_value == 0 & quantity == 0")
    group_null = plus_price_data.loc[plus_price_data[filter_name].isnull(), :]
    plus_price_data = plus_price_data.dropna(subset=[filter_name])
    group_zero = plus_price_data[plus_price_data[filter_name] == 0]
    group_one = plus_price_data.query("{} > 0 & {} <= 100".format(filter_name, filter_name))
    group_two = plus_price_data.query("{} > 100 & {} <= 200".format(filter_name, filter_name))
    group_three = plus_price_data[plus_price_data[filter_name] > 200]
    groups = [
        (-1, group_null),
        (0, abnormal_inventory),
        (1, group_zero),
        (2, group_one),
        (3, group_two),
        (4, group_three),
        (5, minus_price_data)
    ]
    # print(group_one.sort_values("sort_value", ascending=False).head(5000))
    # print(group_one.head(-100))
    return groups


def init_remote_files_downloader(shop_name_abbr):
    if shop_name_abbr == "BL":
        price_file_filter = time.strftime("%Y-%m-%d", time.localtime())
        reference_file_filter = time.strftime("%Y%m%d", time.localtime())

        price_downloader = {
            "hostname": "10.40.0.150",
            "username": "ubuntu",
            "password": "ubuntu!",
            "port": 22,
            "remote_dir": '/home/ubuntu/newused/sources'
        }

        reference_downloader = {
            "hostname": "10.40.0.152",
            "username": "ubuntu",
            "password": "ubuntu!",
            "port": 22,
            "remote_dir": '/home/ubuntu/ecommerceapp/src/inven_site/bookloves'
        }

        downloaders = [
            ("price", price_downloader, price_file_filter),
            ("reference", reference_downloader, reference_file_filter)
        ]
        return downloaders

    elif shop_name_abbr == "ST":
        # price_file_filter = time.strftime("%Y-%m-%d", time.localtime())
        price_file_filter = "source_isbn_price\.db$"

        reference_file_filter = time.strftime("%Y%m%d", time.localtime())
        # reference_file_filter = '20200312.csv'

        # price1_downloader = {
        #     "hostname": "10.45.0.63",
        #     "username": "rsrnd",
        #     "password": "rsrnd@2018",
        #     "port": 22,
        #     "remote_dir": '/home/rsrnd/newused/sources'
        # }
        # price2_downloader = {
        #     "hostname": "10.40.0.152",
        #     "username": "ubuntu",
        #     "password": "ubuntu!",
        #     "port": 22,
        #     "remote_dir": '/home/ubuntu/newused/sources'
        # }

        price_downloader = {
            "hostname": "10.40.0.150",
            "username": "ubuntu",
            "password": "ubuntu!",
            "port": 22,
            "remote_dir": '/home/ubuntu/st_seller_engine/datas/db/book'
        }

        # reference_downloader = {
        #     "hostname": "10.40.0.151",
        #     "username": "TaskClient",
        #     "password": "shenai1224",
        #     "port": 22,
        #     "remote_dir": '/home/TaskClient/AutoProductInfo/ProductReferenceInfo'
        # }

        reference_downloader = {
            "hostname": "10.40.0.152",
            "username": "ubuntu",
            "password": "ubuntu!",
            "port": 22,
            "remote_dir": '/home/ubuntu/ecommerceapp/src/inven_site/stevensbooks'
        }

        downloaders = [
            # ("price1", price1_downloader, price_file_filter),
            # ("price2", price2_downloader, price_file_filter),
            ("price", price_downloader, price_file_filter),
            ("reference", reference_downloader, reference_file_filter)
        ]
        return downloaders

    elif shop_name_abbr == "WL":
        price_file_filter = time.strftime("%Y-%m-%d", time.localtime())
        reference_file_filter = time.strftime("%Y%m%d", time.localtime())

        price_downloader = {
            "hostname": "10.40.0.151",
            "username": "ubuntu",
            "password": "ubuntu!",
            "port": 22,
            "remote_dir": '/home/ubuntu/newused/sources'
        }

        reference_downloader = {
            "hostname": "10.40.0.152",
            "username": "ubuntu",
            "password": "ubuntu!",
            "port": 22,
            "remote_dir": '/home/ubuntu/ecommerceapp/src/inven_site/thebookwelove'
        }

        downloaders = [
            ("price", price_downloader, price_file_filter),
            ("reference", reference_downloader, reference_file_filter)
        ]
        return downloaders

    elif shop_name_abbr == "TS":
        price_file_filter = time.strftime("%Y-%m-%d", time.localtime())
        reference_file_filter = time.strftime("%Y%m%d", time.localtime())

        price_downloader = {
            "hostname": "10.40.0.151",
            "username": "ubuntu",
            "password": "ubuntu!",
            "port": 22,
            "remote_dir": '/home/ubuntu/newused/sources'
        }

        reference_downloader = {
            "hostname": "10.40.0.152",
            "username": "ubuntu",
            "password": "ubuntu!",
            "port": 22,
            "remote_dir": '/home/ubuntu/ecommerceapp/src/inven_site/topsellerbook'
        }

        downloaders = [
            ("price", price_downloader, price_file_filter),
            ("reference", reference_downloader, reference_file_filter)
        ]
        return downloaders

    elif shop_name_abbr == "OL":
        price_file_filter = time.strftime("%Y-%m-%d", time.localtime())
        reference_file_filter = time.strftime("%Y%m%d", time.localtime())

        price_downloader = {
            "hostname": "10.40.0.151",
            "username": "ubuntu",
            "password": "ubuntu!",
            "port": 22,
            "remote_dir": '/home/ubuntu/newused/sources'
        }

        reference_downloader = {
            "hostname": "10.40.0.152",
            "username": "ubuntu",
            "password": "ubuntu!",
            "port": 22,
            "remote_dir": '/home/ubuntu/ecommerceapp/src/inven_site/oliversstore'
        }

        downloaders = [
            ("price", price_downloader, price_file_filter),
            ("reference", reference_downloader, reference_file_filter)
        ]
        return downloaders

    else:
        price_file_filter = time.strftime("%Y-%m-%d", time.localtime())
        reference_file_filter = time.strftime("%Y%m%d", time.localtime())

        price_downloader = {
            "hostname": "10.40.0.150",
            "username": "ubuntu",
            "password": "ubuntu!",
            "port": 22,
            "remote_dir": '/home/ubuntu/newused/sources'
        }

        reference_downloader = {
            "hostname": "10.40.0.152",
            "username": "ubuntu",
            "password": "ubuntu!",
            "port": 22,
            "remote_dir": '/home/ubuntu/ecommerceapp/src/inven_site/bookloves'
        }

        downloaders = [
            ("price", price_downloader, price_file_filter),
            ("reference", reference_downloader, reference_file_filter)
        ]
        return downloaders


def init_files_manager(root_path, shop_name_abbr, date_str):
    price_list_columns = ["id", "site", "isbn", "product_id", "variant_id", "sku", "basic_price", "price_note", "crawl_time"]
    reference_list_columns = ["product_id", "variant_id", "sku", "condition_isbn", "old_price", "quantity", "filter"]
    remote_download_files_dir = os.path.join(root_path, "download_files", shop_name_abbr)
    update_price_files_dir = os.path.join(root_path, "price_update_files", shop_name_abbr)
    log_record_files_dir = os.path.join(root_path, "log_record_files", date_str)
    # log_record_files_dir = "{}/log_record_files/{}".format(root_path, shop_name_abbr)
    price_save_name = "{}_update_price_list_{}.csv".format(shop_name_abbr.lower(), date_str)
    log_save_name = "{}_log_{}.txt".format(shop_name_abbr.lower(), date_str)
    files_dir_manager = {
        "DownloadFilesDir": remote_download_files_dir,
        "PriceFilesDir": update_price_files_dir,
        "LogFilesDir": log_record_files_dir,
        "PriceSave": price_save_name,
        "LogSave": log_save_name,
        "PriceColumns": price_list_columns,
        "ReferenceColumns": reference_list_columns
    }
    return files_dir_manager


def price_special_case_manager(merged_data, case=None, init_size=0):
    default_max_size = 50000
    limit_size = default_max_size - init_size
    if case == "OldPriceMissing":
        null_data_list = merged_data.loc[merged_data["old_price"].isnull(), :]
        normal_data_list = merged_data.dropna(subset=["old_price"])
        norma_size = normal_data_list.shape[0]
        if norma_size >= limit_size:
            mix_merged_data = normal_data_list
        else:
            null_data_size = limit_size - norma_size
            null_data_list.fillna({"old_price": pd.np.nan, "quantity": 3}, inplace=True)
            null_data_list = null_data_list.sort_values("basic_price")
            null_data_list = null_data_list.head(null_data_size)
            mix_merged_data = pd.merge(null_data_list, normal_data_list, how="outer")
    elif case == "AddMinusPrice":
        normal_data_list, minus_price_data = merged_data
        if limit_size > 0:
            minus_price_data = minus_price_data.sort_values("basic_price", ascending=False)
            minus_price_data = minus_price_data.head(limit_size)
            mix_merged_data = pd.merge(normal_data_list, minus_price_data, how="outer")
        else:
            mix_merged_data = normal_data_list
    else:
        if isinstance(merged_data, tuple):
            mix_merged_data, _ = merged_data
        else:
            mix_merged_data = merged_data

    return mix_merged_data
