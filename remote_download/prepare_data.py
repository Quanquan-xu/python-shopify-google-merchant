# -*- coding: utf-8 -*-
import pandas
import os
import re
import time
from remote_download.database import Databases


class PrepareData:
    @staticmethod
    def run(shop_name_abbr="ST", date_str=time.strftime("%Y%m%d", time.localtime())):
        target_dir = os.path.dirname(__file__) + '/download_files/ST'
        price_file_filter = "^{}_{}_{}.+\.db$".format(shop_name_abbr, "price", date_str).lower()
        reference_file_filter = "^{}_{}_{}.+\.txt$".format(shop_name_abbr, "reference", date_str).lower()

        list_files = os.listdir(target_dir)
        price_columns = ["isbn10", "basic_price", "condition"]
        reference_columns = ["site", "product_id", "variant_id", "old_price",
                             "quantity", "isbn10", "condition"]
        price_list = pandas.DataFrame(columns=price_columns)
        reference = pandas.DataFrame(columns=reference_columns)
        for f in list_files:
            if re.search(r'{}'.format(price_file_filter), f):
                database = Databases(os.path.join(target_dir, f))
                tables = database.get_database_tables_name()
                if len(tables) == 1:
                    table = tables[0]
                    database.set_delegate_table_name(table)
                    results = database.query_table_info()
                    data = pandas.DataFrame(results, columns=price_columns)
                    data['condition'] = table.split("_")[1]
                    price_list = price_list.append(data)
            elif re.search(r'{}'.format(reference_file_filter), f):
                original_reference = pandas.read_csv(os.path.join(target_dir, f), sep="\t")
                original_reference = original_reference[
                    ['productid', 'variantid', "price", "quantity", "asin_condition"]]
                original_reference['site'] = "ST"
                original_reference['isbn10'] = original_reference['asin_condition'].apply(lambda x: x.split("_")[0])
                original_reference['condition'] = original_reference['asin_condition'].apply(lambda x: x.split("_")[1])
                data = original_reference[
                    ['site', 'productid', 'variantid', "price", "quantity", "isbn10", "condition"]]
                data.columns = reference_columns
                reference = reference.append(data)
            else:
                pass
        merged_data = pandas.merge(reference, price_list, how='left', on=['isbn10', 'condition'])
        new_product_size = merged_data[merged_data['basic_price'].isnull()].shape[0]
        print("New adding product size: {}".format(new_product_size))
        # merged_data['basic_price'] = merged_data['basic_price'].apply(lambda x: 0 if x != x else x)
        merged_data['basic_price'] = merged_data['basic_price'].apply(lambda x: 0 if x == 'None' else x)
        price_list = merged_data[["site", "product_id", "variant_id", "basic_price"]]
        price_list_file_name = "{}_{}_{}.csv".format(shop_name_abbr, "price", date_str).lower()

        reference = merged_data[["product_id", "variant_id", "old_price", "quantity"]]
        reference_file_name = "{}_{}_{}.csv".format(shop_name_abbr, "reference", date_str).lower()

        price_list.to_csv(os.path.join(target_dir, price_list_file_name), index=False, sep='\t')
        reference.to_csv(os.path.join(target_dir, reference_file_name), index=False, sep='\t')
        list_files = os.listdir(target_dir)
        for f in list_files:
            if f not in [price_list_file_name, reference_file_name]:
                os.remove(os.path.join(target_dir, f))
                pass
