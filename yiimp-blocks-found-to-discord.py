#!/usr/bin/python3

import asyncio
import sys
import logging
import datetime
import argparse
from contextlib import suppress
import aiohttp
from bs4 import BeautifulSoup


async def parse_events(html, queue, share_state_d):

    logger = logging.getLogger('parse_events')

    soup = BeautifulSoup(html, 'html5lib')
    table = soup.find('table')

    if not table:
        logger.error('Unable to find table element in HTML')
        return

    for row in table.findAll('tr')[1:][::-1]:
        col = row.findAll('td')
        coin = col[2].getText()
        coin_amount = float(coin. split(' ')[0])
        coin_name = ' '.join(coin. split(' ')[1:])
        time = col[5].find('span').attrs['title']
        dt = datetime.datetime.strptime(time, '%Y-%m-%d %H:%M:%S')
        # Seems YIIMP first adds the block withtout the coin amount
        # Next iteration get the proper amount
        if dt > share_state_d['previous_poll_dt'] and coin_amount != 0:
            logger.info('New event found while parsing: %f %s found at %s', coin_amount, coin_name, dt)
            queue.put_nowait((dt, coin_name, coin_amount))
            share_state_d['previous_poll_dt'] = dt


async def refresh_stocks_exchange_markets(url, d_markets):

    logger = logging.getLogger('refresh_st_exc_markets')

    try:
        while True:
            try:
                # Compat with older aiohttp version not implementing __aexit__
                # https://stackoverflow.com/a/37467388/8998305
                with aiohttp.ClientSession() as session:
                    resp = await session.get(url)
                    try:
                        assert resp.status_code == 200, 'aiohttp call to %s failed' % url
                        d_resp = await resp.json()
                    except Exception as e:
                        resp.close()
                        raise e
                    finally:
                        await resp.release()
                    new_d_markets = { tuple(x['market_name'].split('_')): float(x['buy']) for x in d_resp }
                    # Keep reference
                    d_markets.update(new_d_markets)
                logger.info('Refreshed')
                await asyncio.sleep(60)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.exception('Exception occurred: %s: %s', e.__class__.__name__, e)
                await asyncio.sleep(60)

    except asyncio.CancelledError:
        logger.info('Exiting on cancel signal')
        return


async def refresh_cryptopia_markets(url, d_markets):

    logger = logging.getLogger('refresh_cryptopia_markets')

    try:
        while True:
            try:
                # Compat with older aiohttp version not implementing __aexit__
                # https://stackoverflow.com/a/37467388/8998305
                with aiohttp.ClientSession() as session:
                    resp = await session.get(url)
                    try:
                        assert resp.status_code == 200, 'aiohttp call to %s failed' % url
                        d_resp = await resp.json()
                    except Exception as e:
                        resp.close()
                        raise e
                    finally:
                        await resp.release()
                    new_d_markets = { tuple(x['Label'].split('/')): float(x['LastPrice']) for x in d_resp['Data'] }
                    # Keep reference
                    d_markets.update(new_d_markets)
                logger.info('Refreshed')
                await asyncio.sleep(60)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.exception('Exception occurred: %s: %s', e.__class__.__name__, e)
                await asyncio.sleep(60)

    except asyncio.CancelledError:
        logger.info('Exiting on cancel signal')
        return


async def poll_yiimp_events(url, queue):

    logger = logging.getLogger('poll_yiimp_events')
    # Use a dict here, easier to keep reference by updating
    share_state_d = dict()
    share_state_d['previous_poll_dt'] = datetime.datetime.utcnow()
    # For testing purpose
    #share_state_d['previous_poll_dt'] = share_state_d['previous_poll_dt'] - datetime.timedelta(minutes=240)

    # Give other coroutines enought time to refresh markets prices
    with suppress(asyncio.CancelledError):
        await asyncio.sleep(5)

    try:
        while True:
            try:
                # Compat with older aiohttp version not implementing __aexit__
                # https://stackoverflow.com/a/37467388/8998305
                with aiohttp.ClientSession() as session:
                    resp = await session.get(url)
                    try:
                        assert resp.status_code == 200, 'aiohttp call to %s failed' % url
                        html = await resp.text()
                    except Exception as e:
                        resp.close()
                        raise e
                    finally:
                        await resp.release()
                await parse_events(html, queue, share_state_d)
                await asyncio.sleep(60)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.exception('Exception occurred: %s: %s', e.__class__.__name__, e)
                await asyncio.sleep(5)

    except asyncio.CancelledError:
        logger.info('Exiting on cancel signal')
        return


async def post_events_discord(url, queue, d_markets_stocks_exchange, d_markets_cryptopia):

    logger = logging.getLogger('post_events_discord')

    try:
        while True:

            try:
                dt, coin_name, coin_amount = await queue.get()

                message = '%f %s found at %s UTC' % (coin_amount, coin_name, dt)

                # Attempt to convert coin value in BTC
                if (coin_name, 'BTC') in d_markets_cryptopia:
                    coin_amount_btc = coin_amount * d_markets_cryptopia[(coin_name, 'BTC')]
                    message += ' (Cryptopia: %fBTC)' % coin_amount_btc
                elif (coin_name, 'BTC') in d_markets_stocks_exchange:
                    coin_amount_btc = coin_amount * d_markets_stocks_exchange[(coin_name, 'BTC')]
                    message += ' (StocksExc: %fBTC)' % coin_amount_btc
                else:
                    coin_amount_btc = None

                # Attempt to convert BTC coin value in USDT
                if coin_amount_btc is not None:
                    if ('BTC', 'USDT') in d_markets_cryptopia:
                         coin_amount_usdt = coin_amount_btc * d_markets_cryptopia[('BTC', 'USDT')]
                         message += ' (Cryptopia: %fUSDT)' % coin_amount_usdt
                    else:
                        coin_amount_btc = None

                # Compat with older aiohttp version not implementing __aexit__
                # https://stackoverflow.com/a/37467388/8998305
                with aiohttp.ClientSession() as session:
                    resp = await session.post(url, { 'content': message })
                    try:
                        assert resp.status_code == 200, 'aiohttp call to %s failed' % url
                    except Exception as e:
                        resp.close()
                        raise e
                    finally:
                        await resp.release()

                logger.info('Message "%s" successfully posted to Discord', message)

            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.exception('Exception occurred: %s: %s', e.__class__.__name__, e)

    except asyncio.CancelledError:
        logger.info('Exiting on cancel signal')
        return


if __name__ == '__main__':

    queue = asyncio.Queue()
    loop = asyncio.get_event_loop()

    logging.basicConfig(level=logging.INFO, format='%(levelname)-8s [%(name)-25s] %(message)s', stream=sys.stdout)
    logger = logging.getLogger('main')

    d_markets_stocks_exchange = dict()
    d_markets_cryptopia = dict()

    def cli_arguments():
        parser = argparse.ArgumentParser(description='Service polling YIIMP pool to output found blocks on Discord (with currency conversion)')
        parser.add_argument('-p', '--pool-url',    required=True, type=str, help='YIIMP pool url to block found page',     metavar='http://yiimp.eu/site/found_results')
        parser.add_argument('-d', '--discord-url', required=True, type=str, help='Discord webhook url to publish message', metavar='https://discordapp.com/api/webhooks/123456/abdHD76Hhdhngga')
        return parser.parse_args()

    config = cli_arguments()

    pool_url = config.pool_url
    discord_url = config.discord_url
    stocks_exchange_url = 'https://stocks.exchange/api2/prices'
    cryptopia_url = 'https://www.cryptopia.co.nz/api/GetMarkets'

    try:
        logger.info('Starting refresh_stock_exchange_markets')
        refresh_stocks_exchange_markets_coro = loop.create_task(refresh_stocks_exchange_markets(stocks_exchange_url, d_markets_stocks_exchange))

        logger.info('Starting refresh_cryptopia_markets')
        refresh_cryptopia_markets_coro = loop.create_task(refresh_cryptopia_markets(cryptopia_url, d_markets_cryptopia))

        logger.info('Starting poll_yiimp_events coroutine')
        poll_yiimp_events_coro = loop.create_task(poll_yiimp_events(pool_url, queue))

        logger.info('Starting post_events_discord coroutine')
        post_events_discord_coro = loop.create_task(post_events_discord(discord_url, queue, d_markets_stocks_exchange, d_markets_cryptopia))

        loop.run_until_complete(asyncio.gather(poll_yiimp_events_coro,
                                               post_events_discord_coro,
                                               refresh_cryptopia_markets_coro,
                                               refresh_stocks_exchange_markets_coro,
                                              ))

    except KeyboardInterrupt:
        all_tasks = asyncio.Task.all_tasks()
        logger.info('Exit signal received, stopping %d coroutines', len(all_tasks))
        for task in all_tasks:
            task.cancel()
        loop.run_until_complete(asyncio.wait_for(asyncio.gather(*all_tasks), timeout=10))

    loop.close()
