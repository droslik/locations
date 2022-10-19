import json
import aiohttp
import asyncio
from geopy.geocoders import Nominatim
from bs4 import BeautifulSoup


def get_location(address):
    geolocator = Nominatim(user_agent="my_request")
    location = geolocator.geocode(address)
    try:
        lat = location.latitude
        long = location.longitude
        if lat and long:
            return lat, long
    except:
        AttributeError(f'{address} not found')
    return None


def get_info():
    list_of_shops = [64106, 64067, 64068, 64069, 64070, 64071,
                     131067, 133702, 136241, 256331, 539467,
                     120882, 151877, 64072, 408658, 278351,
                     146332, 354764, 398172, 454325, 311526,
                     431729, 507705, 614211, 552624]
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    task = loop.create_task(main(list_of_shops))
    async_result = loop.run_until_complete(task)
    return async_result


async def create_one_task(session, shop):
    async with session.get(
            f'https://www.som1.ru/shops/{shop}/', ssl=False
    ) as response_from_shop:
        if response_from_shop.status == 200:
            data_shop = response_from_shop
            soup_shop = BeautifulSoup(await data_shop.text(), 'lxml')
            shop_name = soup_shop.find('title').text
            info = soup_shop.find(
                'table', class_='shop-info-table'
            ).findAll('td')
            shop_address = info[2].text
            shop_phones = info[5].text.split(',')
            shop_schedule = info[8].text
            latlon = get_location(shop_address)

        data = {'address': shop_address,
                'latlon': latlon,
                'name': shop_name,
                'phones': shop_phones,
                'working_hours': shop_schedule
                }
        return data


async def get_all_tasks(session, list_of_shops):
    tasks = []
    for shop in list_of_shops:
        task = asyncio.create_task(create_one_task(session, shop))
        tasks.append(task)
    results = await asyncio.gather(*tasks)
    return results


async def main(list_of_shops):
    async with aiohttp.ClientSession(trust_env=True) as session:
        response = await get_all_tasks(session, list_of_shops)
        json_data = json.dumps(response, ensure_ascii=False)
        with open('shops_som1.json', 'w') as file:
            file.write(json_data)


if __name__ == '__main__':
    get_info()
