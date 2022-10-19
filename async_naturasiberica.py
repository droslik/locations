import json
import aiohttp
import asyncio
from geopy.geocoders import Nominatim
import requests
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
    response_from_main_page = requests.get(
        'https://naturasiberica.ru/our-shops/'
    )
    data = response_from_main_page.text
    soup = BeautifulSoup(data, 'lxml')
    name = soup.find('div', class_='footer__copyright').text.strip()[12:27]
    class_card_list = soup.findAll('a', class_='card-list__link')
    addresses_raw = soup.findAll('p', class_='card-list__description')
    addresses = [
        address.text.splitlines()[-2].strip('\t') +
        address.text.splitlines()[-1].strip('\t')
        for address in addresses_raw
    ]
    list_of_shops_urls_endings = [a['href'][11:] for a in class_card_list]
    data_dict = dict(zip(list_of_shops_urls_endings, addresses))
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    task = loop.create_task(main(name, data_dict))
    async_result = loop.run_until_complete(task)
    return async_result


async def create_one_task(session, name, key, value):
    async with session.get(
            f'https://naturasiberica.ru/our-shops/{key}', ssl=False
    ) as response_from_shop:
        data_shop = response_from_shop
        soup_shop = BeautifulSoup(await data_shop.text(), 'lxml')
        schedule_shop = soup_shop.find(
            'div', class_='shop-schedule original-shops__schedule'
        ).text.splitlines()
        working_hours = [
            ' '.join(schedule_shop[0:2]).strip(),
            ' '.join(schedule_shop[2:]).strip()
        ]
        address = value
        name = name
        location = get_location(address)
        data = {
            'address': address,
            'latlon': location,
            'name': name,
            'phones': [],
            'working_hours': working_hours
        }
        return data


async def get_all_tasks(session, name, data_dict):
    tasks = []
    for key, value in data_dict.items():
        task = asyncio.create_task(create_one_task(session, name, key, value))
        tasks.append(task)
    results = await asyncio.gather(*tasks)
    return results


async def main(name, data_dict):
    async with aiohttp.ClientSession(trust_env=True) as session:
        response = await get_all_tasks(session, name, data_dict)
        json_data = json.dumps(response, ensure_ascii=False)
        with open('shops_naturasiberica.json', 'w') as file:
            file.write(json_data)


if __name__ == '__main__':
    get_info()
