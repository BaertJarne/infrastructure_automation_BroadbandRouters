# imports
import csv
import time
from netmiko import ConnectHandler

# variables
file = 'Br_config.csv'
settings_router = {
    "device_type": "cisco_ios",
    "host": "192.168.10.3",
    "username": "cisco",
    "password": "cisco",
    "port": 22,  # optional, defaults to 22
    "global_cmd_verify": False
    }

# def's
def create_file_name_txt():
    txt_name = file.replace('.csv', '.txt')
    return txt_name

def create_txt_file():
    name = create_file_name_txt()

    data = csv_to_br_config()
    with open(name, 'w') as txt_file:
        txt_file.write(data)
    # net_connect.send_command(data, read_timeout=30)
    # time.sleep(10)
    # show_output = net_connect.send_command("show ip int brief")
    # print(show_output)

def read_csv_file():
    try:
        with open(file, 'r') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=';')
            csv_data = [row for row in csv_reader]
            return csv_data
    except FileNotFoundError:
        print(f"Error: The file '{file}' was not found.")
        return []
    except Exception as e:
        print(f"An error occurred: {e}")
        return []

def csv_to_br_config():
    txt_data = 'ena\nconf t\nhostname Br\nend\n'
    txt_data += convert_csv_data_to_config()
    txt_data += 'end\nwr\n'
    return txt_data

def convert_csv_data_to_config():
    csv_data = read_csv_file()
    txt_data = ''

    print(f"CSV Data: {csv_data}")  # Debugging line to check the CSV data

    csv_data = csv_data[1:]  # Skip the header row

    for row in csv_data:
        txt_data += 'conf t\n'
        # network,interface,description,vlan,ipaddress,subnetmask,defaultgateway
        network = row[0].strip()
        interface = row[1].strip()
        description = row[2].strip()
        vlan = row[3].strip()
        ip_address = row[4].strip()
        netmask = row[5].strip()
        gateway = row[6].strip()

        txt_data += f'int {interface}\n'
        if description:
            txt_data += f'description {description}\n'

        if network.lower() == 'wan':
            if ip_address == 'dhcp' or not ip_address:
                txt_data += 'ip address dhcp\n'
            elif not netmask:
                raise ValueError(f'Missing subnet mask for WAN row: {row}')
            else:
                txt_data += f'ip address {ip_address} {netmask}\n'
            txt_data += 'ip nat outside\n'
            txt_data += 'no shut\n!\nexit\n'
            txt_data += f'ip route 0.0.0.0 0.0.0.0 {gateway}\n'
        else:
            if vlan not in ('', '0'):
                txt_data += f'encapsulation dot1Q {vlan}\n'
            if ip_address and ip_address != 'dhcp':
                if not netmask:
                    raise ValueError(f'Missing subnet mask for LAN row: {row}')
                txt_data += f'ip address {ip_address} {netmask}\n'
            txt_data += 'ip nat inside\n'
        
            if gateway and gateway != 'dhcp' and ip_address and netmask:
                txt_data += f'ip dhcp pool {row["description"] or "LAN"}\n'
                txt_data += f'network {ip_address} {netmask}\n'
                txt_data += f'default-router {gateway}\n'
        
        txt_data += 'no shut\n!\n'
    
        txt_data += 'ip nat inside source list 1 interface gi0/0 overload\n'
        txt_data += 'access-list 1 permit 192.168.0.0 0.0.255.255\n'

        if not network:
            raise ValueError(f"Invalid data in CSV row: {row}")

        txt_data += 'no shut\nend\n'

    print(f"Generated TXT Data: {txt_data}")  # Debugging line to check the generated TXT data
    return txt_data

# flow
# net_connect = ConnectHandler(**settings_router)
create_txt_file()