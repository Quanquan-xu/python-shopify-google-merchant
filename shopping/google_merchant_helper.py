# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function
from shopping.content import _constants
import googleapiclient
import json
import re
import time
import os
import shopify
import pandas as pd
from shopping.content import common
from six.moves import range
from shopify_lib.shopify_to_google_merchant import ShopifyToGoogleMerchant
from config.configuration import variant_merchant_check, free_shipping_check, init_files_manager


class GoogleMerchantHelper:
    def __init__(self, store_name_abbr):
        self.batch_size = 250
        self.max_page_size = 250
        self.merchant_name = store_name_abbr
        self.shop_helper = ShopifyToGoogleMerchant(store_name_abbr)
        self._service, self._config, _ = common.init([os.path.dirname(__file__)], __doc__, store_name=self.merchant_name)
        self._merchant_id = self._config['merchantId']
        self.variant_merchant_check = variant_merchant_check(self.merchant_name)
        self.free_shipping_check = free_shipping_check(self.merchant_name)

        self.date_str = time.strftime("%Y%m%d", time.localtime())
        self.root_path = os.path.dirname(__file__)
        files_manager = init_files_manager(self.root_path, store_name_abbr, self.date_str)
        self.log_files_dir = files_manager.get("LogFilesDir")
        self.log_file_name = files_manager.get("LogSave")
        if not os.path.exists(self.log_files_dir):
            os.makedirs(self.log_files_dir)

    def _init_update_log_record(self, num=None, page=None, end=None, size=None, note=None):
        if num or page or size:
            time_stamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            data = [num, page, end, size, note, time_stamp]
        else:
            data = None
        log_record_file = os.path.join(self.log_files_dir, self.log_file_name)
        log_columns = ["num", "page", "end", "size", "note", "time"]
        if os.path.exists(log_record_file):
            log_data = pd.read_csv(log_record_file, delimiter="\t")
        else:
            log_data = pd.DataFrame(columns=log_columns)

        if not data:
            if log_data.empty:
                page_start = 1
            else:
                log_size = log_data.shape[0]
                last_page_start = log_data["page"].tolist()[-1]
                last_note = log_data["note"].tolist()[-1]
                if last_note == "Done":
                    page_start = last_page_start + 1
                else:
                    page_start = last_page_start

                if log_size >= 2:
                    up_page_start = log_data["page"].tolist()[-2]
                    up_note = log_data["note"].tolist()[-2]
                    if up_page_start == last_page_start and up_note == up_note:
                        page_start = page_start + 1
            return page_start
        else:
            new_log = pd.DataFrame([data], columns=log_columns)
            log_data = log_data.append(new_log)
            log_data.to_csv(log_record_file, sep="\t", index=False)

    def _product_sample(self, method, product_detail):
        if method == "INSERT":
            product = {
                'offerId':
                    product_detail.get("product_id"),
                'title':
                    product_detail.get("title"),
                "brand": product_detail.get("brand"),
                'description':
                    product_detail.get("description"),
                'link':
                    product_detail.get("link"),
                'contentLanguage':
                    _constants.CONTENT_LANGUAGE,
                'targetCountry':
                    _constants.TARGET_COUNTRY,
                'channel':
                    _constants.CHANNEL,
                'availability':
                    product_detail.get("availability"),
                'condition':
                    product_detail.get("condition"),
                # 'googleProductCategory':
                #     'Media > Books',
                'mpn': product_detail.get("mpn"),
                'price': {
                    'value': product_detail.get("price"),
                    'currency': 'USD'},
                'shippingWeight': {
                    'value': product_detail.get("weight"),
                    'unit': 'grams'},
                'shippingLabel':
                    "Free Shipping" if self.free_shipping_check else 'standard shipping',
                'taxes': [
                    {'country': 'US', 'taxShip': True, 'rate': 0.0},
                    {'country': 'MX', 'taxShip': True, 'rate': 16.0},
                    {'country': 'UK', 'taxShip': True, 'rate': 20.0},
                    {'country': 'US', 'taxShip': True, 'rate': 4.0, 'region': 'AL'},
                    {'country': 'US', 'taxShip': True, 'rate': 0.0, 'region': 'AK'},
                    {'country': 'US', 'taxShip': True, 'rate': 0.0, 'region': 'AS'},
                    {'country': 'US', 'taxShip': True, 'rate': 5.6, 'region': 'AZ'},
                    {'country': 'US', 'taxShip': True, 'rate': 6.5, 'region': 'AR'},
                    {'country': 'US', 'taxShip': True, 'rate': 0.0, 'region': 'AA'},
                    {'country': 'US', 'taxShip': True, 'rate': 0.0, 'region': 'AE'},
                    {'country': 'US', 'taxShip': True, 'rate': 0.0, 'region': 'AP'},
                    {'country': 'US', 'taxShip': True, 'rate': 7.5, 'region': 'CA'},
                    {'country': 'US', 'taxShip': True, 'rate': 2.9, 'region': 'CO'},
                    {'country': 'US', 'taxShip': True, 'rate': 6.35, 'region': 'CT'},
                    {'country': 'US', 'taxShip': True, 'rate': 0.0, 'region': 'DE'},
                    {'country': 'US', 'taxShip': True, 'rate': 5.75, 'region': 'DC'},
                    {'country': 'US', 'taxShip': True, 'rate': 0.0, 'region': 'FM'},
                    {'country': 'US', 'taxShip': True, 'rate': 6.0, 'region': 'FL'},
                    {'country': 'US', 'taxShip': True, 'rate': 4.0, 'region': 'GA'},
                    {'country': 'US', 'taxShip': True, 'rate': 0.0, 'region': 'GU'},
                    {'country': 'US', 'taxShip': True, 'rate': 4.0, 'region': 'HI'},
                    {'country': 'US', 'taxShip': True, 'rate': 6.0, 'region': 'ID'},
                    {'country': 'US', 'taxShip': True, 'rate': 6.25, 'region': 'IL'},
                    {'country': 'US', 'taxShip': True, 'rate': 7.0, 'region': 'IN'},
                    {'country': 'US', 'taxShip': True, 'rate': 6.0, 'region': 'IA'},
                    {'country': 'US', 'taxShip': True, 'rate': 6.5, 'region': 'KS'},
                    {'country': 'US', 'taxShip': True, 'rate': 6.0, 'region': 'KY'},
                    {'country': 'US', 'taxShip': True, 'rate': 4.0, 'region': 'LA'},
                    {'country': 'US', 'taxShip': True, 'rate': 5.5, 'region': 'ME'},
                    {'country': 'US', 'taxShip': True, 'rate': 0.0, 'region': 'MH'},
                    {'country': 'US', 'taxShip': True, 'rate': 6.0, 'region': 'MD'},
                    {'country': 'US', 'taxShip': True, 'rate': 6.25, 'region': 'MA'},
                    {'country': 'US', 'taxShip': True, 'rate': 6.0, 'region': 'MI'},
                    {'country': 'US', 'taxShip': True, 'rate': 6.875, 'region': 'MN'},
                    {'country': 'US', 'taxShip': True, 'rate': 7.0, 'region': 'MS'},
                    {'country': 'US', 'taxShip': True, 'rate': 4.225, 'region': 'MO'},
                    {'country': 'US', 'taxShip': True, 'rate': 0.0, 'region': 'MT'},
                    {'country': 'US', 'taxShip': True, 'rate': 5.5, 'region': 'NE'},
                    {'country': 'US', 'taxShip': True, 'rate': 6.85, 'region': 'NV'},
                    {'country': 'US', 'taxShip': True, 'rate': 0.0, 'region': 'NH'},
                    {'country': 'US', 'taxShip': True, 'rate': 7.0, 'region': 'NJ'},
                    {'country': 'US', 'taxShip': True, 'rate': 5.0, 'region': 'NM'},
                    {'country': 'US', 'taxShip': True, 'rate': 4.0, 'region': 'NY'},
                    {'country': 'US', 'taxShip': True, 'rate': 4.75, 'region': 'NC'},
                    {'country': 'US', 'taxShip': True, 'rate': 5.0, 'region': 'ND'},
                    {'country': 'US', 'taxShip': True, 'rate': 0.0, 'region': 'MP'},
                    {'country': 'US', 'taxShip': True, 'rate': 5.75, 'region': 'OH'},
                    {'country': 'US', 'taxShip': True, 'rate': 4.5, 'region': 'OK'},
                    {'country': 'US', 'taxShip': True, 'rate': 0.0, 'region': 'OR'},
                    {'country': 'US', 'taxShip': True, 'rate': 0.0, 'region': 'PW'},
                    {'country': 'US', 'taxShip': True, 'rate': 6.0, 'region': 'PA'},
                    {'country': 'US', 'taxShip': True, 'rate': 10.5, 'region': 'PR'},
                    {'country': 'US', 'taxShip': True, 'rate': 7.0, 'region': 'RI'},
                    {'country': 'US', 'taxShip': True, 'rate': 5.0, 'region': 'SC'},
                    {'country': 'US', 'taxShip': True, 'rate': 4.0, 'region': 'SD'},
                    {'country': 'US', 'taxShip': True, 'rate': 7.0, 'region': 'TN'},
                    {'country': 'US', 'taxShip': True, 'rate': 6.25, 'region': 'TX'},
                    {'country': 'US', 'taxShip': True, 'rate': 4.7, 'region': 'UT'},
                    {'country': 'US', 'taxShip': True, 'rate': 6.0, 'region': 'VT'},
                    {'country': 'US', 'taxShip': True, 'rate': 0.0, 'region': 'VI'},
                    {'country': 'US', 'taxShip': True, 'rate': 5.3, 'region': 'VA'},
                    {'country': 'US', 'taxShip': True, 'rate': 6.5, 'region': 'WA'},
                    {'country': 'US', 'taxShip': True, 'rate': 6.0, 'region': 'WV'},
                    {'country': 'US', 'taxShip': True, 'rate': 5.0, 'region': 'WI'},
                    {'country': 'US', 'taxShip': True, 'rate': 4.0, 'region': 'WY'}]
            }
            if product_detail.get("images"):
                images_list = product_detail.get("images").split(";")
                product['imageLink'] = images_list[0]
                if len(images_list) >= 2:
                    product['additionalImageLinks'] = images_list[1:10]
            if product_detail.get("product_type"):
                product_type = product_detail.get("product_type")
                product['productType'] = product_type
                if len(product_type.split(">")) >= 2:
                    pass
            return product
        elif method == "OTHER":
            pass
        else:
            pass
            self.batch_size = 2

    def product_insert_batch(self, product_list):

        batch_groups = [product_list[i:i + self.batch_size] for i in range(0, len(product_list), self.batch_size)]
        print(len(batch_groups))
        for group in batch_groups:
            batch_size = self.batch_size if self.batch_size <= len(group) else len(group)
            print(batch_size)
            batch = {
                'entries': [{
                    'batchId': i,
                    'merchantId': self._merchant_id,
                    'method': 'insert',
                    'product': self._product_sample("INSERT", group[i]),
                } for i in range(batch_size)],
            }
            # print(batch)
            request = self._service.products().custombatch(body=batch)
            result = request.execute()
            if result['kind'] == 'content#productsCustomBatchResponse':
                entries = result['entries']
                for entry in entries:
                    product = entry.get('product')
                    errors = entry.get('errors')
                    if product:
                        print('Product "%s" with offerId "%s" was created.' %
                              (product['id'], product['offerId']))
                    elif errors:
                        print('Errors for batch entry %d:' % entry['batchId'])
                        print(json.dumps(errors, sort_keys=True, indent=2,
                                         separators=(',', ': ')))
            else:
                print('There was an error. Response: %s' % result)

    def product_list_query(self):
        request = self._service.products().list(
            merchantId=self._merchant_id, maxResults=self.max_page_size)

        while request is not None:
            result = request.execute()
            products = result.get('resources')
            if not products:
                print('No products were found.')
                break
            print("Page:")
            product_ids = []
            for product in products:
                product_ids.append(product['id'])
                print('Product "%s" with brand "%s"; mpn "%s" ;link "%s"was found.' %
                      (product['id'].split(":")[-1], product.get('brand'), product.get('mpn'), product['link']))
                print("#"*30)
                if product.get('gtin') or not product.get('brand'):
                    print('Product "%s" with gtin "%s"; price "%s" ;link "%s"was found.' %
                          (product['id'].split(":")[-1], product.get('gtin'), product.get('mpn'), product['link']))
                    print("#"*30)
                #     self.product_delete(product['id'])
                # self.product_delete(product['id'])
            # self.product_delete_batch(product_ids)
            # break
            request = self._service.products().list_next(request, result)

    def product_update_price_batch(self, product_list, group=2):
        if 0 <= int(group) <= 1:
            product_ids = [product.get("productId") for product in product_list]
            self.product_delete_batch(product_ids)
        else:
            batch_groups = [product_list[i:i + self.batch_size] for i in range(0, len(product_list), self.batch_size)]
            print("{}--Batch groups: {}".format(self.merchant_name, len(batch_groups)))
            for products in batch_groups:
                batch = {
                    'entries': [{
                        'batchId': i,
                        'merchantId': self._merchant_id,
                        'storeCode': "online",
                        'productId': product.get("productId"),
                        'inventory': product.get("inventory"),
                    } for i, product in enumerate(products)],
                }
                request = self._service.inventory().custombatch(body=batch)
                result = request.execute()

                if result['kind'] == 'content#inventoryCustomBatchResponse':
                    entries = result['entries']
                    non_exist_product_id_list = []
                    non_exist_variant_id_list = []
                    error_product_id_list = []
                    for entry in entries:
                        errors = entry.get('errors')
                        if errors:
                            # print('Errors for batch entry %d:' % entry['batchId'])
                            error_json = json.dumps(errors, sort_keys=True, indent=2, separators=(',', ': '))
                            # print(error_json)
                            product = products[entry['batchId']]
                            product_id = product.get("product_id")
                            variant_id = product.get("variant_id")
                            if re.search(r"\"message\": \"cannot update inventory of non-existing product\"",
                                         error_json):
                                print("Cannot update inventory of non-existing product")
                                non_exist_product_id_list.append(product_id)
                                non_exist_variant_id_list.append(variant_id)
                            else:
                                print(error_json)
                                error_product_id_list.append(product_id)
                        else:
                            print('Successfully performed inventory update for product "%s".' %
                                  (products[entry['batchId']]))
                    if self.variant_merchant_check:
                        non_exist_variant_id_list = None
                    if non_exist_product_id_list:
                        add_product_list = self.shop_helper.retrieve_product_merchant_info_by_ids(
                            non_exist_product_id_list,
                            non_exist_variant_id_list)
                        self.product_insert_batch(add_product_list)
                else:
                    print('There was an error. Response: %s' % result)

    def product_update_link(self, product_list):
        for product in product_list:
            product_id = product.get("product_id")
            variant_id = product.get("variant_id")
            try:
                product = self._service.products().get(
                    merchantId=self._merchant_id, productId=product_id).execute()
                old_link = product['link']
                old_variant_id = old_link.split("?variant=")[-1]
                link_prefix = old_link.split("?variant=")[0]
                if str(old_variant_id) != str(variant_id):
                    print("Old variant id :{}".format(old_variant_id))
                    print(old_link)
                    product['link'] = link_prefix + "?variant=" + str(variant_id)
                    print(product['link'])
                    print('Product with offerId "%s" and link "%s" was updated.' %
                          (product_id, variant_id))
                    # request = self._service.products().insert(merchantId=self._merchant_id, body=product)
                    # result = request.execute()
                    # print('Product with offerId "%s" and link "%s" was updated.' %
                    #       (result['offerId'], result['link']))
            except googleapiclient.errors.HttpError:
                print("Product was not found")

    def product_update_expiration_date(self, product_id_list):
        for product_id in product_id_list:
            try:
                product = self._service.products().get(
                    merchantId=self._merchant_id, productId=product_id).execute()
                product['expirationDate'] = time.strftime('%Y-%m-%dT%H:%M:%SZ',
                                                          time.gmtime(time.time() + 3600 * 24 * int(60)))
                request = self._service.products().insert(merchantId=self._merchant_id, body=product)
                result = request.execute()
                print('Product with offerId "%s" and link "%s" was updated.' % (result['offerId'], result['link']))
            except googleapiclient.errors.HttpError:
                print("Product was not found")

    def _product_update_images(self, product_list):
        for product in product_list:
            product_id = product.get("product_id")
            images_list = product.get("images")
            try:
                product = self._service.products().get(
                    merchantId=self._merchant_id, productId=product_id).execute()
                if images_list:
                    product['imageLink'] = images_list[0]
                    request = self._service.products().insert(merchantId=self._merchant_id, body=product)
                    result = request.execute()
                    print('Product with offerId "%s" and imageLink "%s" was updated.' %
                          (result['offerId'], result['imageLink']))
            except googleapiclient.errors.HttpError:
                print("Product was not found")

    def product_delete(self, product_id):
        request = self._service.products().delete(
            merchantId=self._merchant_id, productId=product_id)
        request.execute()
        print('Product %s was deleted.' % product_id)

    def product_delete_batch(self, product_ids):
        batch = {
            'entries': [{
                'batchId': i,
                'merchantId': self._merchant_id,
                'method': 'delete',
                'productId': v,
            } for i, v in enumerate(product_ids)],
        }

        request = self._service.products().custombatch(body=batch)
        result = request.execute()

        if result['kind'] == 'content#productsCustomBatchResponse':
            for entry in result['entries']:
                errors = entry.get('errors')
                if errors:
                    print('Errors for batch entry %d:' % entry['batchId'])
                    print(json.dumps(entry['errors'], sort_keys=True, indent=2,
                                     separators=(',', ': ')))
                else:
                    print('Deletion of product %s (batch entry %d) successful.' %
                          (batch['entries'][entry['batchId']]['productId'],
                           entry['batchId']))

        else:
            print('There was an error. Response: %s' % result)

    def product_status_list_query(self):
        common.check_mca(self._config, False)

        request = self._service.productstatuses().list(
            merchantId=self._merchant_id, maxResults=self.max_page_size)

        while request is not None:
            result = request.execute()
            statuses = result.get('resources')
            if not statuses:
                print('No product statuses were returned.')
                break
            for stat in statuses:
                print('- Product "%s" with title "%s":' %
                      (stat['productId'], stat['title']))
                print(json.dumps(stat, sort_keys=True, indent=2, separators=(',', ': ')))
            request = self._service.productstatuses().list_next(request, result)

    def product_list(self):
        common.check_mca(self._config, True)
        request = self._service.accountstatuses().list(
            merchantId=self._merchant_id, maxResults=self.max_page_size)

        while request is not None:
            result = request.execute()
            statuses = result.get('resources')
            if not statuses:
                print('No statuses were returned.')
                break
            for status in statuses:
                print('Account %s:' % status['accountId'])
                issues = status.get('dataQualityIssues')
                if not issues:
                    print('- No data quality issues.')
                    continue
                print('- Found %d data quality issues:' % len(issues))
                for issue in issues:
                    print('  - (%s) [%s]' % (issue['severity'], issue['id']))
                    items = issue.get('exampleItems')
                    if not items:
                        print('    No example items.')
                        continue
                    print('    Have %d examples from %d affected items:' %
                          (len(items), issue['numItems']))
                    for example in items:
                        print('    - %s: %s' % (example['itemId'], example['title']))
            request = self._service.accountstatuses().list_next(request, result)

    def resubmit_product_to_merchant_by_all_pages(self, start_page=1, end_page=None):
        page_start = self._init_update_log_record()
        if page_start > start_page:
            start_page = page_start
        resource_count = shopify.Product.count()
        print(resource_count)
        pages = int(resource_count / 250) + 1
        if not end_page:
            end_page = pages
        for page in range(start_page, end_page+1):
            print("page{}".format(page))
            try:
                if self.variant_merchant_check:
                    merchant_info_list = self.shop_helper.retrieve_product_variants_merchant_info_by_page(page)
                    self.product_insert_batch(merchant_info_list)
                else:
                    merchant_info_list = self.shop_helper.retrieve_product_merchant_info_by_page(page)
                    self.product_insert_batch(merchant_info_list)

            except Exception as e:
                error_note = str(e)
                self._init_update_log_record(resource_count, page, end_page, pages, error_note)
                raise TypeError("Something Wrong")
            else:
                self._init_update_log_record(resource_count, page, end_page, pages, "Done")

    def retrieve_product_to_merchant_by_all_pages(self):
        resource_count = shopify.Product.count()
        print(resource_count)
        pages = int(resource_count / 250) + 1
        for page in range(1, pages+1):
            print("page{}".format(page))
            merchant_info_list = self.shop_helper.retrieve_product_merchant_info_by_page(page)
            self.product_insert_batch(merchant_info_list)

    def retrieve_product_variants_to_merchant_by_all_pages(self):
        resource_count = shopify.Product.count()
        print(resource_count)
        pages = int(resource_count / 250) + 1
        for page in range(1, pages + 1):
            print("page{}".format(page))
            merchant_info_list = self.shop_helper.retrieve_product_variants_merchant_info_by_page(page)
            self.product_insert_batch(merchant_info_list)

