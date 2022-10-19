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
    except: AttributeError(f'{address} not found')
    return None


def get_info():
    response_from_main_page = requests.get(
        'https://oriencoop.cl/sucursales.htm'
    )
    data = response_from_main_page.text
    soup = BeautifulSoup(data, 'lxml')
    common_phones = [
        phone.text for phone in soup.find(
            'div', class_='b-call shadow'
        ).findAll('a', href=True) if phone.text
    ]
    c_list_accordion_class = soup.findAll('ul', class_='sub-menu')
    list_of_ul = []
    for i in c_list_accordion_class:
        list_of_ul.append(i.findAllNext('a', href=True))
    list_of_branches = [
        a['href'][12:] for a in list_of_ul[0] if '/sucursales/' in a['href']
    ]
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    task = loop.create_task(main(list_of_branches, common_phones))
    async_result = loop.run_until_complete(task)
    return async_result


async def create_one_task(session, branch, common_phones):
    async with session.get(
         f'https://oriencoop.cl/sucursales/{int(branch)}', ssl=False
         ) as response_from_branch:
        data_branch = response_from_branch
        soup_branch = BeautifulSoup(await data_branch.text(), 'lxml')
        s_dato_info = soup_branch.find('div', class_="s-dato").findAll('span')
        address = s_dato_info[0].text
        branch_phone = [s_dato_info[1].text]
        for common_phone in common_phones:
            branch_phone.append(common_phone)
        working_hours = s_dato_info[3].text[1:], s_dato_info[4].text.strip()
        name = [img['alt'] for img in soup_branch.find(
            'div', class_='b-logo'
        ).find_all('img', alt=True)][0]
        location = get_location(address)
        data = {
            'address': address,
                'latlon': location,
                'name': name,
                'phones': branch_phone,
                'working_hours': working_hours
        }
        return data


async def get_all_tasks(session, list_of_branches, common_phones):
    tasks = []
    for branch in list_of_branches:
        task = asyncio.create_task(
            create_one_task(session, branch, common_phones)
        )
        tasks.append(task)
    results = await asyncio.gather(*tasks)
    return results


async def main(list_of_branches, common_phones):
    async with aiohttp.ClientSession(trust_env=True) as session:
        response = await get_all_tasks(
            session, list_of_branches, common_phones
        )
        json_data = json.dumps(response, ensure_ascii=False)
        with open('sucursales_branches.json', 'w') as file:
            file.write(json_data)


if __name__ == '__main__':
    get_info()
