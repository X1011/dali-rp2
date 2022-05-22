# Copyright 2022 macanudo527
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
from typing import Any

from dateutil import parser
from rp2.rp2_decimal import RP2Decimal

from dali.dali_configuration import Keyword
from dali.in_transaction import InTransaction
from dali.intra_transaction import IntraTransaction
from dali.out_transaction import OutTransaction
from dali.plugin.input.rest.binance_com import InputPlugin


class TestBinance:

    # pylint: disable=no-self-use
    def test_deposits(self, mocker: Any) -> None:
        plugin = InputPlugin(
            account_holder="tester",
            api_key="a",
            api_secret="b",
            native_fiat="USD",
        )

        mocker.patch.object(plugin.client, "sapiGetFiatPayments").return_value = {
            "code": "000000",
            "message": "success",
            "data": [
                {
                    "orderNo": "353fca443f06466db0c4dc89f94f027a",
                    "sourceAmount": "20.0",  # Fiat trade amount
                    "fiatCurrency": "EUR",  # Fiat token
                    "obtainAmount": "4.462",  # Crypto trade amount
                    "cryptoCurrency": "LUNA",  # Crypto token
                    "totalFee": "0.2",  # Trade fee
                    "price": "4.437472",
                    "status": "Completed",  # Processing, Completed, Failed, Refunded
                    "createTime": 1624529919000,
                    "updateTime": 1624529919000,
                },
                {
                    "orderNo": "353fca443f06466db0c4dc89f94f027b",
                    "sourceAmount": "40.0",  # Fiat trade amount
                    "fiatCurrency": "EUR",  # Fiat token
                    "obtainAmount": "8.924",  # Crypto trade amount
                    "cryptoCurrency": "LUNA",  # Crypto token
                    "totalFee": "0.4",  # Trade fee
                    "price": "4.437472",
                    "status": "Failed",  # Processing, Completed, Failed, Refunded
                    "createTime": 1624529920000,
                    "updateTime": 1624529920000,
                },
            ],
            "total": 2,
            "success": True,
        }

        mocker.patch.object(plugin, "start_time_ms", int(datetime.datetime.now().timestamp()) * 1000 - 1)
        mocker.patch.object(plugin.client, "fetch_deposits").return_value = [
            {
                "info": {
                    "amount": "0.00999800",
                    "coin": "PAXG",
                    "network": "ETH",
                    "status": "1",
                    "address": "0x788cabe9236ce061e5a892e1a59395a81fc8d62c",
                    "addressTag": "",
                    "txId": "0xaad4654a3234aa6118af9b4b335f5ae81c360b2394721c019b5d1e75328b09f3",
                    "insertTime": "1599621997000",
                    "transferType": "0",
                    "confirmTimes": "12/12",
                    "unlockConfirm": "12/12",
                    "walletType": "0",
                },
                "id": None,
                "txid": "0xaad4654a3234aa6118af9b4b335f5ae81c360b2394721c019b5d1e75328b09f3",
                "timestamp": 1599621997000,
                "datetime": "2020-09-09T03:26:37.000Z",
                "network": "ETH",
                "address": "0x788cabe9236ce061e5a892e1a59395a81fc8d62c",
                "addressTo": "0x788cabe9236ce061e5a892e1a59395a81fc8d62c",
                "addressFrom": None,
                "tag": None,
                "tagTo": None,
                "tagFrom": None,
                "type": "deposit",
                "amount": 0.00999800,
                "currency": "PAXG",
                "status": "ok",
                "updated": None,
                "internal": False,
                "fee": None,
            }
        ]

        mocker.patch.object(plugin.client, "sapiGetFiatOrders").return_value = {
            "code": "000000",
            "message": "success",
            "data": [
                {
                    "orderNo": "25ced37075c1470ba8939d0df2316e23",
                    "fiatCurrency": "EUR",
                    "indicatedAmount": "15.00",
                    "amount": "14.80",
                    "totalFee": "0.20",
                    "method": "card",
                    "status": "Completed",
                    "createTime": 1627501026000,
                    "updateTime": 1627501027000,
                },
                {
                    "orderNo": "25ced37075c1470ba8939d0df2316e24",
                    "fiatCurrency": "EUR",
                    "indicatedAmount": "30.00",
                    "amount": "29.60",
                    "totalFee": "0.40",
                    "method": "card",
                    "status": "Failed",
                    "createTime": 1627501028000,
                    "updateTime": 1627501029000,
                },
            ],
            "total": 2,
            "success": True,
        }

        mocker.patch.object(plugin, "_process_trades").return_value = None
        mocker.patch.object(plugin, "_process_gains").return_value = None
        mocker.patch.object(plugin, "_process_withdrawals").return_value = None

        result = plugin.load()

        # 1 completed Fiat Payment +
        # 1 crypto Transfer +
        # 1 fiat deposit = 3
        assert len(result) == 3

        fiat_in_transaction: InTransaction = result[0]  # type: ignore
        crypto_deposit_transaction: IntraTransaction = result[2]  # type: ignore
        fiat_deposit: InTransaction = result[1]  # type: ignore

        assert fiat_in_transaction.asset == "LUNA"
        assert int(parser.parse(fiat_in_transaction.timestamp).timestamp()) * 1000 == 1624529919000
        assert fiat_in_transaction.transaction_type == Keyword.BUY.value
        assert RP2Decimal(fiat_in_transaction.spot_price) == RP2Decimal("20.0") / RP2Decimal("4.462")
        assert RP2Decimal(fiat_in_transaction.crypto_in) == RP2Decimal("4.462")
        assert fiat_in_transaction.crypto_fee is None
        assert RP2Decimal(str(fiat_in_transaction.fiat_in_no_fee)) == RP2Decimal("20.0")
        assert RP2Decimal(str(fiat_in_transaction.fiat_in_with_fee)) == RP2Decimal("19.8")
        assert RP2Decimal(str(fiat_in_transaction.fiat_fee)) == RP2Decimal("0.2")
        # assert fiat_in_transaction.fiat_iso_code == "EUR"

        assert crypto_deposit_transaction.asset == "PAXG"
        assert int(parser.parse(crypto_deposit_transaction.timestamp).timestamp()) * 1000 == 1599621997000
        assert crypto_deposit_transaction.from_exchange == Keyword.UNKNOWN.value
        assert crypto_deposit_transaction.to_exchange == "Binance.com"
        assert crypto_deposit_transaction.crypto_sent == Keyword.UNKNOWN.value
        assert RP2Decimal(crypto_deposit_transaction.crypto_received) == RP2Decimal("0.00999800")

        assert fiat_deposit.asset == "EUR"
        assert int(parser.parse(fiat_deposit.timestamp).timestamp()) * 1000 == 1627501026000
        assert fiat_deposit.transaction_type == Keyword.BUY.value
        assert RP2Decimal(fiat_deposit.spot_price) == RP2Decimal("1")
        assert RP2Decimal(fiat_deposit.crypto_in) == RP2Decimal("15.00")
        assert RP2Decimal(str(fiat_deposit.crypto_fee)) == RP2Decimal("0.20")
        assert fiat_deposit.fiat_in_no_fee is None
        assert fiat_deposit.fiat_in_with_fee is None
        assert fiat_deposit.fiat_fee is None

    # pylint: disable=no-self-use
    def test_trades(self, mocker: Any) -> None:
        plugin = InputPlugin(
            account_holder="tester",
            api_key="a",
            api_secret="b",
            native_fiat="USD",
        )

        plugin.markets = ["ETHBTC"]

        mocker.patch.object(plugin.client, "fetch_my_trades").return_value = [
            # Trade using BNB for fee payment
            {
                "info": {"sample": "data"},  # the original decoded JSON as is
                "id": "12345-67890:09876/54321",  # string trade id
                "timestamp": 1502962946000,  # Unix timestamp in milliseconds
                "datetime": "2017-08-17 12:42:48.000",  # ISO8601 datetime with milliseconds
                "symbol": "ETH/BTC",  # symbol
                "order": "12345-67890:09876/54321",  # string order id or undefined/None/null
                "type": "limit",  # order type, 'market', 'limit' or undefined/None/null
                "side": "buy",  # direction of the trade, 'buy' or 'sell'
                "takerOrMaker": "taker",  # string, 'taker' or 'maker'
                "price": 0.06917684,  # float price in quote currency
                "amount": 1.5,  # amount of base currency
                "cost": 0.10376526,  # total cost, `price * amount`,
                "fee": {  # provided by exchange or calculated by ccxt
                    "cost": 0.0015,  # float
                    "currency": "BNB",  # usually base currency for buys, quote currency for sells
                    "rate": 0.002,  # the fee rate (if available)
                },
            },
            # Trade using the quote currency for fee payment
            {
                "info": {"sample": "data"},  # the original decoded JSON as is
                "id": "12345-67890:09876/54321",  # string trade id
                "timestamp": 1502962947000,  # Unix timestamp in milliseconds
                "datetime": "2017-08-17 12:42:48.000",  # ISO8601 datetime with milliseconds
                "symbol": "ETH/BTC",  # symbol
                "order": "12345-67890:09876/54321",  # string order id or undefined/None/null
                "type": "limit",  # order type, 'market', 'limit' or undefined/None/null
                "side": "buy",  # direction of the trade, 'buy' or 'sell'
                "takerOrMaker": "taker",  # string, 'taker' or 'maker'
                "price": 0.06917684,  # float price in quote currency
                "amount": 3,  # amount of base currency
                "cost": 0.20753052,  # total cost, `price * amount`,
                "fee": {  # provided by exchange or calculated by ccxt
                    "cost": 0.0015,  # float
                    "currency": "ETH",  # usually base currency for buys, quote currency for sells
                    "rate": 0.002,  # the fee rate (if available)
                },
            },
            # Sell trade using the quote currency for fee payment
            {
                "info": {"sample": "data"},  # the original decoded JSON as is
                "id": "12345-67890:09876/54321",  # string trade id
                "timestamp": 1502962948000,  # Unix timestamp in milliseconds
                "datetime": "2017-08-17 12:42:48.000",  # ISO8601 datetime with milliseconds
                "symbol": "ETH/BTC",  # symbol
                "order": "12345-67890:09876/54321",  # string order id or undefined/None/null
                "type": "limit",  # order type, 'market', 'limit' or undefined/None/null
                "side": "sell",  # direction of the trade, 'buy' or 'sell'
                "takerOrMaker": "taker",  # string, 'taker' or 'maker'
                "price": 0.06917684,  # float price in quote currency
                "amount": 6,  # amount of base currency
                "cost": 0.41506104,  # total cost, `price * amount`,
                "fee": {  # provided by exchange or calculated by ccxt
                    "cost": 0.0015,  # float
                    "currency": "BTC",  # usually base currency for buys, quote currency for sells
                    "rate": 0.002,  # the fee rate (if available)
                },
            },
            # Fiat Buy
            {
                "info": {"sample": "data"},  # the original decoded JSON as is
                "id": "12345-67890:09876/54321",  # string trade id
                "timestamp": 1502962949000,  # Unix timestamp in milliseconds
                "datetime": "2017-08-17 12:42:48.000",  # ISO8601 datetime with milliseconds
                "symbol": "BTC/GBP",  # symbol
                "order": "12345-67890:09876/54321",  # string order id or undefined/None/null
                "type": "limit",  # order type, 'market', 'limit' or undefined/None/null
                "side": "buy",  # direction of the trade, 'buy' or 'sell'
                "takerOrMaker": "taker",  # string, 'taker' or 'maker'
                "price": 23000.01,  # float price in quote currency
                "amount": 1,  # amount of base currency
                "cost": 23000.01,  # total cost, `price * amount`,
                "fee": {  # provided by exchange or calculated by ccxt
                    "cost": 0.002,  # float
                    "currency": "BTC",  # usually base currency for buys, quote currency for sells
                    "rate": 0.002,  # the fee rate (if available)
                },
            },
            # Fiat Sell
            {
                "info": {"sample": "data"},  # the original decoded JSON as is
                "id": "12345-67890:09876/54321",  # string trade id
                "timestamp": 1502962950000,  # Unix timestamp in milliseconds
                "datetime": "2017-08-17 12:42:48.000",  # ISO8601 datetime with milliseconds
                "symbol": "BTC/GBP",  # symbol
                "order": "12345-67890:09876/54321",  # string order id or undefined/None/null
                "type": "limit",  # order type, 'market', 'limit' or undefined/None/null
                "side": "sell",  # direction of the trade, 'buy' or 'sell'
                "takerOrMaker": "taker",  # string, 'taker' or 'maker'
                "price": 23000.01,  # float price in quote currency
                "amount": 1,  # amount of base currency
                "cost": 23000.01,  # total cost, `price * amount`,
                "fee": {  # provided by exchange or calculated by ccxt
                    "cost": 40,  # float
                    "currency": "GBP",  # usually base currency for buys, quote currency for sells
                    "rate": 0.002,  # the fee rate (if available)
                },
            },
        ]

        # CCXT abstracts dust trades into regular trades, so no testing is necessary
        mocker.patch.object(plugin.client, "fetch_my_dust_trades").return_value = []
        mocker.patch.object(plugin, "_process_deposits").return_value = None
        mocker.patch.object(plugin, "_process_gains").return_value = None
        mocker.patch.object(plugin, "_process_withdrawals").return_value = None

        result = plugin.load()

        # One Sell of quote asset (using BNB) +
        # One Buy of base asset (using BNB) +
        # One payment for fees in BNB
        # One Sell of quote asset (for Buy order) +
        # One Buy of base asset (for Buy order) +
        # One Sell of quote asset (for Sell order) +
        # One Buy of base asset (for Sell order) +
        # One Buy of base asset (for fiat buy) +
        # One Sell of quote asset (for fiat buy) +
        # One Sell of quote asset (for fiat sell) +
        # One Buy of base asset (for fiat buy) = 11
        assert len(result) == 11

        bnb_sell_transaction: OutTransaction = result[5]  # type: ignore
        bnb_buy_transaction: InTransaction = result[0]  # type: ignore
        bnb_fee_transaction: OutTransaction = result[6]  # type: ignore
        buy_conversion_out: OutTransaction = result[7]  # type: ignore
        buy_conversion_in: InTransaction = result[1]  # type: ignore
        sell_conversion_order_out: OutTransaction = result[8]  # type: ignore
        sell_conversion_order_in: InTransaction = result[2]  # type: ignore
        buy_fiat_order_out: OutTransaction = result[9]  # type: ignore
        buy_fiat_order_in: InTransaction = result[3]  # type: ignore
        sell_fiat_order_out: OutTransaction = result[10]  # type: ignore
        sell_fiat_order_in: InTransaction = result[4]  # type: ignore

        # Buy with BNB as fee payment
        assert bnb_sell_transaction.asset == "BTC"
        assert int(parser.parse(bnb_sell_transaction.timestamp).timestamp()) * 1000 == 1502962946000
        assert bnb_sell_transaction.transaction_type == Keyword.SELL.value
        assert bnb_sell_transaction.spot_price == Keyword.UNKNOWN.value
        assert RP2Decimal(bnb_sell_transaction.crypto_out_no_fee) == RP2Decimal("0.10376526")
        assert RP2Decimal(bnb_sell_transaction.crypto_fee) == RP2Decimal("0")
        assert RP2Decimal(str(bnb_sell_transaction.crypto_out_with_fee)) == RP2Decimal("0.10376526")
        assert bnb_sell_transaction.fiat_out_no_fee is None
        assert bnb_sell_transaction.fiat_fee is None

        assert bnb_buy_transaction.asset == "ETH"
        assert int(parser.parse(bnb_buy_transaction.timestamp).timestamp()) * 1000 == 1502962946000
        assert bnb_buy_transaction.transaction_type == Keyword.BUY.value
        assert bnb_buy_transaction.spot_price == Keyword.UNKNOWN.value
        assert RP2Decimal(bnb_buy_transaction.crypto_in) == RP2Decimal("1.5")
        assert RP2Decimal(str(bnb_buy_transaction.crypto_fee)) == RP2Decimal("0")
        assert bnb_buy_transaction.fiat_in_no_fee is None
        assert bnb_buy_transaction.fiat_in_with_fee is None
        assert bnb_buy_transaction.fiat_fee is None

        assert bnb_fee_transaction.asset == "BNB"
        assert int(parser.parse(bnb_fee_transaction.timestamp).timestamp()) * 1000 == 1502962946000
        assert bnb_fee_transaction.transaction_type == Keyword.FEE.value
        assert bnb_fee_transaction.spot_price == Keyword.UNKNOWN.value
        assert RP2Decimal(bnb_fee_transaction.crypto_out_no_fee) == RP2Decimal("0.0015")
        assert RP2Decimal(bnb_fee_transaction.crypto_fee) == RP2Decimal("0")
        assert RP2Decimal(str(bnb_fee_transaction.crypto_out_with_fee)) == RP2Decimal("0.0015")
        assert bnb_fee_transaction.fiat_out_no_fee is None
        assert bnb_fee_transaction.fiat_fee is None

        # Buy with base asset as fee payment
        assert buy_conversion_out.asset == "BTC"
        assert int(parser.parse(buy_conversion_out.timestamp).timestamp()) * 1000 == 1502962947000
        assert buy_conversion_out.transaction_type == Keyword.SELL.value
        assert buy_conversion_out.spot_price == Keyword.UNKNOWN.value
        assert RP2Decimal(buy_conversion_out.crypto_out_no_fee) == RP2Decimal("0.20753052")
        assert RP2Decimal(buy_conversion_out.crypto_fee) == RP2Decimal("0")
        assert RP2Decimal(str(buy_conversion_out.crypto_out_with_fee)) == RP2Decimal("0.20753052")
        assert buy_conversion_out.fiat_out_no_fee is None
        assert buy_conversion_out.fiat_fee is None

        assert buy_conversion_in.asset == "ETH"
        assert int(parser.parse(buy_conversion_in.timestamp).timestamp()) * 1000 == 1502962947000
        assert buy_conversion_in.transaction_type == Keyword.BUY.value
        assert buy_conversion_in.spot_price == Keyword.UNKNOWN.value
        assert RP2Decimal(buy_conversion_in.crypto_in) == RP2Decimal("2.9985")
        assert RP2Decimal(str(buy_conversion_in.crypto_fee)) == RP2Decimal("0.0015")
        assert buy_conversion_in.fiat_in_no_fee is None
        assert buy_conversion_in.fiat_in_with_fee is None
        assert buy_conversion_in.fiat_fee is None

        # Sell with quote asset as fee payment
        assert sell_conversion_order_out.asset == "ETH"
        assert int(parser.parse(sell_conversion_order_out.timestamp).timestamp()) * 1000 == 1502962948000
        assert sell_conversion_order_out.transaction_type == Keyword.SELL.value
        assert sell_conversion_order_out.spot_price == Keyword.UNKNOWN.value
        assert RP2Decimal(sell_conversion_order_out.crypto_out_no_fee) == RP2Decimal("6")
        assert RP2Decimal(sell_conversion_order_out.crypto_fee) == RP2Decimal("0")
        assert RP2Decimal(str(sell_conversion_order_out.crypto_out_with_fee)) == RP2Decimal("6")
        assert sell_conversion_order_out.fiat_out_no_fee is None
        assert sell_conversion_order_out.fiat_fee is None

        assert sell_conversion_order_in.asset == "BTC"
        assert int(parser.parse(sell_conversion_order_in.timestamp).timestamp()) * 1000 == 1502962948000
        assert sell_conversion_order_in.transaction_type == Keyword.BUY.value
        assert sell_conversion_order_in.spot_price == Keyword.UNKNOWN.value
        assert RP2Decimal(sell_conversion_order_in.crypto_in) == RP2Decimal("0.41356104")
        assert RP2Decimal(str(sell_conversion_order_in.crypto_fee)) == RP2Decimal("0.0015")
        assert sell_conversion_order_in.fiat_in_no_fee is None
        assert sell_conversion_order_in.fiat_in_with_fee is None
        assert sell_conversion_order_in.fiat_fee is None

        # Fiat buy with base asset as a fee
        assert buy_fiat_order_out.asset == "GBP"
        assert int(parser.parse(buy_fiat_order_out.timestamp).timestamp()) * 1000 == 1502962949000
        assert buy_fiat_order_out.transaction_type == Keyword.SELL.value
        assert RP2Decimal(buy_fiat_order_out.spot_price) == RP2Decimal("23000.01")
        assert RP2Decimal(buy_fiat_order_out.crypto_out_no_fee) == RP2Decimal("23000.01")
        assert RP2Decimal(buy_fiat_order_out.crypto_fee) == RP2Decimal("0")
        assert RP2Decimal(str(buy_fiat_order_out.crypto_out_with_fee)) == RP2Decimal("23000.01")
        assert RP2Decimal(str(buy_fiat_order_out.fiat_out_no_fee)) == RP2Decimal("23000.01")
        assert RP2Decimal(str(buy_fiat_order_out.fiat_fee)) == RP2Decimal("0")

        assert buy_fiat_order_in.asset == "BTC"
        assert int(parser.parse(buy_fiat_order_in.timestamp).timestamp()) * 1000 == 1502962949000
        assert buy_fiat_order_in.transaction_type == Keyword.BUY.value
        assert RP2Decimal(buy_fiat_order_in.spot_price) == RP2Decimal("23000.01")
        assert RP2Decimal(buy_fiat_order_in.crypto_in) == RP2Decimal("0.998")
        assert RP2Decimal(str(buy_fiat_order_in.crypto_fee)) == RP2Decimal("0.002")
        assert RP2Decimal(str(buy_fiat_order_in.fiat_in_no_fee)) == RP2Decimal("23000.01")
        assert RP2Decimal(str(buy_fiat_order_in.fiat_in_with_fee)) == RP2Decimal("22954.00998")
        assert buy_fiat_order_in.fiat_fee is None

        # Fiat sell with quote asset as a fee
        assert sell_fiat_order_out.asset == "BTC"
        assert int(parser.parse(sell_fiat_order_out.timestamp).timestamp()) * 1000 == 1502962950000
        assert sell_fiat_order_out.transaction_type == Keyword.SELL.value
        assert RP2Decimal(sell_fiat_order_out.spot_price) == RP2Decimal("23000.01")
        assert RP2Decimal(sell_fiat_order_out.crypto_out_no_fee) == RP2Decimal("1")
        assert RP2Decimal(sell_fiat_order_out.crypto_fee) == RP2Decimal("0")
        assert RP2Decimal(str(sell_fiat_order_out.crypto_out_with_fee)) == RP2Decimal("1")
        assert RP2Decimal(str(sell_fiat_order_out.fiat_out_no_fee)) == RP2Decimal("23000.01")
        assert RP2Decimal(str(sell_fiat_order_out.fiat_fee)) == RP2Decimal("0")

        assert sell_fiat_order_in.asset == "GBP"
        assert int(parser.parse(sell_fiat_order_in.timestamp).timestamp()) * 1000 == 1502962950000
        assert sell_fiat_order_in.transaction_type == Keyword.BUY.value
        assert RP2Decimal(sell_fiat_order_in.spot_price) == RP2Decimal("23000.01")
        assert RP2Decimal(sell_fiat_order_in.crypto_in) == RP2Decimal("22960.01")
        assert RP2Decimal(str(sell_fiat_order_in.crypto_fee)) == RP2Decimal("40")
        assert RP2Decimal(str(sell_fiat_order_in.fiat_in_no_fee)) == RP2Decimal("23000.01")
        assert RP2Decimal(str(sell_fiat_order_in.fiat_in_with_fee)) == RP2Decimal("22960.01")
        assert sell_fiat_order_in.fiat_fee is None

    # pylint: disable=no-self-use
    def test_gains(self, mocker: Any) -> None:
        plugin = InputPlugin(
            account_holder="tester",
            api_key="a",
            api_secret="b",
            native_fiat="USD",
        )

        # Bypassing algo call
        plugin.algos = ["sha256"]
        plugin.username = "user"

        mocker.patch.object(plugin, "start_time_ms", int(datetime.datetime.now().timestamp()) * 1000 - 1)
        mocker.patch.object(plugin.client, "sapiGetAssetAssetDividend").return_value = {
            "rows": [
                {"id": 1637366104, "amount": "0.00001600", "asset": "BETH", "divTime": 1563189166000, "enInfo": "ETH 2.0 Staking", "tranId": 2968885920},
                {"id": 1631750237, "amount": "0.51206985", "asset": "BUSD", "divTime": 1563189165000, "enInfo": "Flexible Savings", "tranId": 2968885920},
            ],
            "total": 2,
        }

        # Only mining type 0 transactions are supported
        mocker.patch.object(plugin.client, "sapiGetMiningPaymentList").return_value = {
            "code": 0,
            "msg": "",
            "data": {
                "accountProfits": [
                    {
                        "time": 1586188800000,  # Mining date
                        "type": 31,  # 0:Mining Wallet,5:Mining Address,7:Pool Savings,8:Transferred,31:Income Transfer ,
                        # 32:Hashrate Resale-Mining Wallet 33:Hashrate Resale-Pool Savings
                        "hashTransfer": None,  # Transferred Hashrate
                        "transferAmount": None,  # Transferred Income
                        "dayHashRate": 129129903378244,  # Daily Hashrate
                        "profitAmount": 8.6083060304,  # Earnings Amount
                        "coinName": "BTC",  # Coin Type
                        "status": 2,  # Status：0:Unpaid， 1:Paying  2：Paid
                    },
                    {
                        "time": 1607529600000,
                        "coinName": "BTC",
                        "type": 0,
                        "dayHashRate": 9942053925926,
                        "profitAmount": 0.85426469,
                        "hashTransfer": 200000000000,
                        "transferAmount": 0.02180958,
                        "status": 2,
                    },
                ],
                "totalNum": 2,  # Total Rows
                "pageSize": 20,  # Rows per page
            },
        }

        mocker.patch.object(plugin, "_process_deposits").return_value = None
        mocker.patch.object(plugin, "_process_trades").return_value = None
        mocker.patch.object(plugin, "_process_withdrawals").return_value = None

        result = plugin.load()

        # One Eth staking transaction +
        # One BUSD savings transaction +
        # One Mining transaction = 3
        assert len(result) == 3

        eth_staking: InTransaction = result[0]  # type: ignore
        busd_savings: InTransaction = result[1]  # type: ignore
        mining_deposit: InTransaction = result[2]  # type: ignore

        # Make sure it identifies this as staking income
        assert eth_staking.asset == "BETH"
        assert int(parser.parse(eth_staking.timestamp).timestamp()) * 1000 == 1563189166000
        assert eth_staking.transaction_type == Keyword.STAKING.value
        assert eth_staking.spot_price == Keyword.UNKNOWN.value
        assert RP2Decimal(eth_staking.crypto_in) == RP2Decimal("0.00001600")
        assert eth_staking.crypto_fee is None
        assert eth_staking.fiat_in_no_fee is None
        assert eth_staking.fiat_in_with_fee is None
        assert eth_staking.fiat_fee is None

        assert busd_savings.asset == "BUSD"
        assert int(parser.parse(busd_savings.timestamp).timestamp()) * 1000 == 1563189165000
        assert busd_savings.transaction_type == Keyword.INTEREST.value
        assert busd_savings.spot_price == Keyword.UNKNOWN.value
        assert RP2Decimal(busd_savings.crypto_in) == RP2Decimal("0.51206985")
        assert busd_savings.crypto_fee is None
        assert busd_savings.fiat_in_no_fee is None
        assert busd_savings.fiat_in_with_fee is None
        assert busd_savings.fiat_fee is None

        assert mining_deposit.asset == "BTC"
        assert int(parser.parse(mining_deposit.timestamp).timestamp()) * 1000 == 1607529600000
        assert mining_deposit.transaction_type == Keyword.MINING.value
        assert mining_deposit.spot_price == Keyword.UNKNOWN.value
        assert RP2Decimal(mining_deposit.crypto_in) == RP2Decimal("0.85426469")
        assert mining_deposit.crypto_fee is None
        assert mining_deposit.fiat_in_no_fee is None
        assert mining_deposit.fiat_in_with_fee is None
        assert mining_deposit.fiat_fee is None

    # pylint: disable=no-self-use
    def test_withdrawls(self, mocker: Any) -> None:
        plugin = InputPlugin(
            account_holder="tester",
            api_key="a",
            api_secret="b",
            native_fiat="USD",
        )

        mocker.patch.object(plugin, "start_time_ms", int(datetime.datetime.now().timestamp()) * 1000 - 1)
        mocker.patch.object(plugin.client, "fetch_withdrawals").return_value = [
            {
                "info": {
                    "amount": "0.00999800",
                    "coin": "PAXG",
                    "network": "ETH",
                    "status": "1",
                    "address": "0x788cabe9236ce061e5a892e1a59395a81fc8d62c",
                    "addressTag": "",
                    "txId": "0xaad4654a3234aa6118af9b4b335f5ae81c360b2394721c019b5d1e75328b09f3",
                    "insertTime": "1599621997000",
                    "transferType": "0",
                    "confirmTimes": "12/12",
                    "unlockConfirm": "12/12",
                    "walletType": "0",
                },
                "id": None,
                "txid": "0xaad4654a3234aa6118af9b4b335f5ae81c360b2394721c019b5d1e75328b09f3",
                "timestamp": 1599621997000,
                "datetime": "2020-09-09T03:26:37.000Z",
                "network": "ETH",
                "address": "0x788cabe9236ce061e5a892e1a59395a81fc8d62c",
                "addressTo": "0x788cabe9236ce061e5a892e1a59395a81fc8d62c",
                "addressFrom": None,
                "tag": None,
                "tagTo": None,
                "tagFrom": None,
                "type": "withdrawal",
                "amount": 0.00999800,
                "currency": "PAXG",
                "status": "ok",
                "updated": None,
                "internal": False,
                "fee": None,
            }
        ]

        mocker.patch.object(plugin.client, "sapiGetFiatOrders").return_value = {
            "code": "000000",
            "message": "success",
            "data": [
                {
                    "orderNo": "25ced37075c1470ba8939d0df2316e23",
                    "fiatCurrency": "EUR",
                    "indicatedAmount": "15.00",
                    "amount": "14.80",
                    "totalFee": "0.20",
                    "method": "card",
                    "status": "Completed",
                    "createTime": 1627501026000,
                    "updateTime": 1627501027000,
                },
                {
                    "orderNo": "25ced37075c1470ba8939d0df2316e24",
                    "fiatCurrency": "EUR",
                    "indicatedAmount": "30.00",
                    "amount": "29.60",
                    "totalFee": "0.40",
                    "method": "card",
                    "status": "Failed",
                    "createTime": 1627501028000,
                    "updateTime": 1627501029000,
                },
            ],
            "total": 2,
            "success": True,
        }

        mocker.patch.object(plugin, "_process_trades").return_value = None
        mocker.patch.object(plugin, "_process_gains").return_value = None
        mocker.patch.object(plugin, "_process_deposits").return_value = None

        result = plugin.load()

        # 1 crypto Transfer +
        # 1 fiat withdrawl = 2
        assert len(result) == 2

        crypto_withdrawal_transaction: IntraTransaction = result[1]  # type: ignore
        fiat_withdrawal: OutTransaction = result[0]  # type: ignore

        assert fiat_withdrawal.asset == "EUR"
        assert int(parser.parse(fiat_withdrawal.timestamp).timestamp()) * 1000 == 1627501026000
        assert fiat_withdrawal.transaction_type == Keyword.SELL.value
        assert RP2Decimal(fiat_withdrawal.spot_price) == RP2Decimal("1")
        assert RP2Decimal(fiat_withdrawal.crypto_out_no_fee) == RP2Decimal("15.00")
        assert RP2Decimal(str(fiat_withdrawal.crypto_fee)) == RP2Decimal("0.20")
        assert fiat_withdrawal.fiat_out_no_fee is None
        assert fiat_withdrawal.fiat_fee is None

        assert crypto_withdrawal_transaction.asset == "PAXG"
        assert int(parser.parse(crypto_withdrawal_transaction.timestamp).timestamp()) * 1000 == 1599621997000
        assert crypto_withdrawal_transaction.to_exchange == Keyword.UNKNOWN.value
        assert crypto_withdrawal_transaction.from_exchange == "Binance.com"
        assert crypto_withdrawal_transaction.crypto_received == Keyword.UNKNOWN.value
        assert RP2Decimal(crypto_withdrawal_transaction.crypto_sent) == RP2Decimal("0.00999800")
