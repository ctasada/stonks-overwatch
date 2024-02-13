import json
import polars as pl

from degiro.utils.degiro import DeGiro
from degiro.models import ProductInfo

from scripts.transactions_report import get_productIds
from degiro_connector.quotecast.tools.chart_fetcher import ChartFetcher
from degiro_connector.quotecast.models.chart import ChartRequest, Interval

import_folder = './import'

def get_products_info(product_ids, json_file_path):
    trading_api = DeGiro.get_client()

    products_info = trading_api.get_products_info(
        product_list=list(set(product_ids)),
        raw=True,
    )

    ## Save the JSON to a file
    data_file = open(json_file_path, 'w')
    data_file.write(json.dumps(products_info, indent = 4))
    data_file.close()

def import_products_info(file_path) -> None:
    with open(file_path) as json_file:
        data = json.load(json_file)

    conv = lambda i : i or None
    for key in data['data']:
        row = data['data'][key]
        try :
            ProductInfo.objects.update_or_create(
                id=int(row['id']),
                name=row['name'],
                isin=row['isin'],
                symbol=row['symbol'],
                contractSize=row['contractSize'],
                productType=row['productType'],
                productTypeId=row['productTypeId'],
                tradable=row['tradable'],
                category=row['category'],
                currency=row['currency'],
                active=row['active'],
                exchangeId=row['exchangeId'],
                onlyEodPrices=row['onlyEodPrices'],
                isShortable=row['isShortable'],
                feedQuality=row.get('feedQuality'),
                orderBookDepth=row.get('orderBookDepth'),
                vwdIdentifierType=row.get('vwdIdentifierType'),
                vwdId=row.get('vwdId'),
                qualitySwitchable=row.get('qualitySwitchable'),
                qualitySwitchFree=row.get('qualitySwitchFree'),
                vwdModuleId=row.get('vwdModuleId'),
                feedQualitySecondary=row.get('feedQualitySecondary'),
                orderBookDepthSecondary=row.get('orderBookDepthSecondary'),
                vwdIdentifierTypeSecondary=row.get('vwdIdentifierTypeSecondary'),
                vwdIdSecondary=row.get('vwdIdSecondary'),
                qualitySwitchableSecondary=row.get('qualitySwitchableSecondary'),
                qualitySwitchFreeSecondary=row.get('qualitySwitchFreeSecondary'),
                vwdModuleIdSecondary=row.get('vwdModuleIdSecondary')
            )
        except Exception as error:
            print(f"Cannot import row: {row}")
            print("Exception: ", error)

def _get_quotation(issueid, period):
    # Retrieve user_token
    trading_api = DeGiro.get_client()
    client_details_table = trading_api.get_client_details()
    # int_account = client_details_table['data']['intAccount']
    user_token = client_details_table['data']['id']

    chart_fetcher = ChartFetcher(user_token=user_token)
    chart_request = ChartRequest(
        culture="nl-NL",
        period=period,
        requestid="1",
        resolution=Interval.P1D,
        series=[
            f"issueid:{issueid}",
            f"price:issueid:{issueid}",
        ],
        tz="Europe/Amsterdam",
    )
    chart = chart_fetcher.get_chart(
        chart_request=chart_request,
        raw=False,
    )

    for series in chart.series:
        if (series.type == 'time'):
            print(pl.DataFrame(data=series.data, orient="row"))


def import_products_quotation(file_path) -> None:
    with open(file_path) as json_file:
        data = json.load(json_file)

    for key in data['data']:
        row = data['data'][key]
        issueId = row.get('vwdIdSecondary', row.get('vwdId'))
        if issueId:
            quotation = _get_quotation(issueId, Interval.P1M)
        else:
            # FIXME: Some stocks DO NOT return the value for getting the Quotes
            print(f"{int(row['id'])} - {row['symbol']} - {issueId}")

def run():
    # product_ids = get_productIds()
    # get_products_info(product_ids, f"{import_folder}/products_info.json")
    # import_products_info(f"{import_folder}/products_info.json")
    import_products_quotation(f"{import_folder}/products_info.json")

if __name__ == '__main__':
    run()