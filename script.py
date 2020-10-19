# -*- coding: utf-8 -*-
from remote_download.auto_update_price import AutoUpdatePrice
import argparse


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='manual to this script')
    parser.add_argument('--name', type=str, default="ST")
    parser.add_argument('--gap-price', type=int, default=2)
    parser.add_argument('--compare', type=str, default=">")
    parser.add_argument('--plus-limit', type=int, default=None)
    parser.add_argument('--minus-limit', type=int, default=-8)
    parser.add_argument('--query', type=str, default=None)
    parser.add_argument('--drop', type=bool, default=True)
    args = parser.parse_args()
    shop_name = args.name
    gap_price = args.gap_price
    plus_limit = args.plus_limit
    minus_limit = args.minus_limit
    compare = args.compare
    query = args.query
    drop_file = args.drop
    print("Update BookStore:   \t\"{}\""
          "\nCondition:   \t new_price - old_price {} {} & new_price - old_price < {}\n"
          "Drop file:    \t {}".format(shop_name, compare, gap_price, minus_limit, drop_file))
    if plus_limit:
        print("Update price range: 0 - {}".format(plus_limit))
    price_updater = AutoUpdatePrice(shop_name, gap_price, compare, plus_limit, minus_limit, query)
    price_updater.auto_update_price(drop_files=drop_file)
