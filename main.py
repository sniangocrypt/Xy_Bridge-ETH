import asyncio
from client import Wallet
from web3 import AsyncWeb3, AsyncHTTPProvider, Web3
from web3.exceptions import TransactionNotFound
from aiohttp import ClientSession
from aiohttp_socks import ProxyConnector  # Для работы с прокси
import json
import time
import random

private_key = "" # ВАШ ПРИВАТНЫЙ КЛЮЧ

value = 0.001   # УКАЖИТЕ КОЛИЧЕСТВО ЭФИРА ДЛЯ ТРАНСФЕРА

slippage = 1   # ПРОСКАЛЬЗОВАНИЕ, МАКСИМАЛЬНАЯ ПОТЕРЯ ПРИ ПЕРЕВОДЕ

QuoteTokenAmount = int(value*1000000000000000000)

what_gas = 500   #Максимальный газ в эфире, при работе не с ЕТХ сетью, похуй какой
rpc = "https://arb1.arbitrum.io/rpc"
rpcOUT = "https://rpc.ankr.com/optimism"
w3_async = AsyncWeb3(AsyncHTTPProvider(f"{rpc}"))  # РПС сети
w3_async_out = AsyncWeb3(AsyncHTTPProvider(f"{rpcOUT}"))
getadres = w3_async.eth.account.from_key(private_key).address
exp = "https://arbiscan.io/tx/"

async def check_balance_value():
    address = f"{getadres}"
    checksum_address = w3_async.to_checksum_address(address)
    balance = await w3_async.eth.get_balance(checksum_address)
    ether_balance = w3_async.from_wei(balance, 'ether')
    if float(ether_balance) - float(value) <= 0:
        print("Недостаточно эфира для свопа")
        exit()



async def check_balance():
    address = f"{getadres}"
    checksum_address = w3_async.to_checksum_address(address)
    balance = await w3_async.eth.get_balance(checksum_address)
    ether_balance = w3_async.from_wei(balance, 'ether')
    print(f"Баланс кошелька {checksum_address}: {ether_balance} ETH")


async def wait_gas():
    w3_async_eth = AsyncWeb3(AsyncHTTPProvider('https://eth.meowrpc.com'))
    gas = await w3_async_eth.eth.gas_price
    gas = w3_async_eth.from_wei(gas, 'gwei')
    print(f"Текущий газ {gas}")
    print()
    while gas > what_gas:
        print(f"Текущий газ {gas}, ожидаю снижение")
        await asyncio.sleep(20)
        if gas < what_gas:
            break


async def xy_swap():
    ChainId = await w3_async.eth.chain_id

    outChainId = await w3_async_out.eth.chain_id

    receiver = Web3.to_checksum_address(getadres)

    async with ClientSession() as session:
        # 1st: get tx data from xy aggregator api
        url = f"https://aggregator-api.xy.finance/v1/buildTx?srcChainId={ChainId}&srcQuoteTokenAddress=0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE&srcQuoteTokenAmount={QuoteTokenAmount}&dstChainId={outChainId}&dstQuoteTokenAddress=0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE&slippage={slippage}&receiver={receiver}&bridgeProvider=yBridge&srcBridgeTokenAddress=0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE&dstBridgeTokenAddress=0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE&swapProviders=OneInch"
        async with session.get(url=url) as response:
            data = await response.json()

    # 2nd: get estimateGas by calling web3 rpc
    estimate_gas = await w3_async.eth.estimate_gas(data["tx"])

    # 3rd: Combine the estimateGas with the tx data
    tx = data["tx"]
    tx["nonce"] = await w3_async.eth.get_transaction_count(getadres)
    tx["gasPrice"]= int((await w3_async.eth.gas_price) * 1.25)
    tx["gas"] = estimate_gas

    # 4th: sign the tx & send it
    tx_signed =  w3_async.eth.account.sign_transaction(tx, private_key)
    tx_hash = await w3_async.eth.send_raw_transaction(tx_signed.rawTransaction)
    print(f"Транзакция отправлена {exp}{tx_hash.hex()}")
    print("Средства придут примерно через 3 минуты, нужно подтвреждения сети дождаться/)")

async def main():
    await check_balance_value()
    await check_balance()
    await wait_gas()
    await xy_swap()

asyncio.run(main())
