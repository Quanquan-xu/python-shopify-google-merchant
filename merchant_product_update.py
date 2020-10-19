# -*- coding: utf-8 -*-
from shopping.auto_update_merchant_product import AutoUpdateMerchantProduct
import argparse


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='manual to this script')
    parser.add_argument('--name', type=str, default="BL")
    parser.add_argument('--start-page', type=int, default=1)
    parser.add_argument('--end-page', type=int, default=None)

    args = parser.parse_args()
    shop_name = args.name
    start_page = args.start_page
    end_page = args.end_page

    print("Merchant Product Update BookStore:  \"{}\"".format(shop_name))
    if end_page:
        print("Update price range: {} - {}".format(start_page, end_page))
    merchant_updater = AutoUpdateMerchantProduct(shop_name, start_page, end_page)
    merchant_updater.run()

