import binascii
import socket
import sys
from collections import OrderedDict
import csv

def send_udp_message(message, address, port):
    message = message.replace(" ", "").replace("\n", "")
    server_address = (address, port)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.sendto(binascii.unhexlify(message), server_address)
        data, _ = sock.recvfrom(4096)
    finally:
        sock.close()
    return binascii.hexlify(data).decode("utf-8")

def build_message(type="A", address=""):
    ID = 43690  
    QR = 0      # Query: 0, Response: 1
    OPCODE = 0  # Standard query       
    AA = 0      # Authoritative Answer          
    TC = 0      # Message is truncated?
    RD = 1      # Recursion Desired        
    RA = 0      # Recursion Available          
    Z = 0       # feature use                    
    RCODE = 0   # Response code             

    query_params = str(QR)
    query_params += str(OPCODE).zfill(4)
    query_params += str(AA) + str(TC) + str(RD) + str(RA)
    query_params += str(Z).zfill(3)
    query_params += str(RCODE).zfill(4)
    query_params = "{:04x}".format(int(query_params, 2))

    QDCOUNT = 1 # questions
    ANCOUNT = 0 # answers
    NSCOUNT = 0 # authority records
    ARCOUNT = 0 # additional records  

    message = ""
    message += "{:04x}".format(ID)
    message += query_params
    message += "{:04x}".format(QDCOUNT)
    message += "{:04x}".format(ANCOUNT)
    message += "{:04x}".format(NSCOUNT)
    message += "{:04x}".format(ARCOUNT)


    addr_parts = address.split(".")
    for part in addr_parts:
        addr_len = "{:02x}".format(len(part))
        addr_part = binascii.hexlify(part.encode())
        message += addr_len
        message += addr_part.decode()

    message += "00" 

    # Type of request
    QTYPE = get_type(type)
    message += QTYPE

    # Class for lookup. 1 is Internet
    QCLASS = 1
    message += "{:04x}".format(QCLASS)

    return message


def decode_message(message):    
    res = []
    
    ID            = message[0:4]
    query_params  = message[4:8]
    QDCOUNT       = message[8:12]
    ANCOUNT       = message[12:16]
    NSCOUNT       = message[16:20]
    ARCOUNT       = message[20:24]

    params = "{:b}".format(int(query_params, 16)).zfill(16)
    QPARAMS = OrderedDict([
        ("QR", params[0:1]),
        ("OPCODE", params[1:5]),
        ("AA", params[5:6]),
        ("TC", params[6:7]),
        ("RD", params[7:8]),
        ("RA", params[8:9]),
        ("Z", params[9:12]),
        ("RCODE", params[12:16])
    ])

    # Question section
    QUESTION_SECTION_STARTS = 24
    question_parts = parse_parts(message, QUESTION_SECTION_STARTS, [])
    
    QNAME = ".".join(map(lambda p: binascii.unhexlify(p).decode(), question_parts))    

    QTYPE_STARTS = QUESTION_SECTION_STARTS + (len("".join(question_parts))) + (len(question_parts) * 2) + 2
    QCLASS_STARTS = QTYPE_STARTS + 4

    QTYPE = message[QTYPE_STARTS:QCLASS_STARTS]
    QCLASS = message[QCLASS_STARTS:QCLASS_STARTS + 4]
    
    res.append("\n# HEADER")
    res.append("ID: " + ID)
    res.append("QUERYPARAMS: ")
    for qp in QPARAMS:
        res.append(" - " + qp + ": " + QPARAMS[qp])
    res.append("\n# QUESTION SECTION")
    res.append("QNAME: " + QNAME)
    res.append("QTYPE: " + QTYPE + " (\"" + get_type(int(QTYPE, 16)) + "\")")
    res.append("QCLASS: " + QCLASS)

    # Answer section
    ANSWER_SECTION_STARTS = QCLASS_STARTS + 4
    
    NUM_ANSWERS = max([int(ANCOUNT, 16), int(NSCOUNT, 16), int(ARCOUNT, 16)])
    if NUM_ANSWERS > 0:
        res.append("\n# ANSWER SECTION")
        
        for ANSWER_COUNT in range(NUM_ANSWERS):
            if (ANSWER_SECTION_STARTS < len(message)):
                ANAME = message[ANSWER_SECTION_STARTS:ANSWER_SECTION_STARTS + 4] # Refers to Question
                ATYPE = message[ANSWER_SECTION_STARTS + 4:ANSWER_SECTION_STARTS + 8]
                ACLASS = message[ANSWER_SECTION_STARTS + 8:ANSWER_SECTION_STARTS + 12]
                TTL = int(message[ANSWER_SECTION_STARTS + 12:ANSWER_SECTION_STARTS + 20], 16)
                RDLENGTH = int(message[ANSWER_SECTION_STARTS + 20:ANSWER_SECTION_STARTS + 24], 16)
                RDDATA = message[ANSWER_SECTION_STARTS + 24:ANSWER_SECTION_STARTS + 24 + (RDLENGTH * 2)]

                if ATYPE == get_type("A"):
                    octets = [RDDATA[i:i+2] for i in range(0, len(RDDATA), 2)]
                    RDDATA_decoded = ".".join(list(map(lambda x: str(int(x, 16)), octets)))
                else:
                    RDDATA_decoded = ".".join(map(lambda p: binascii.unhexlify(p).decode('iso8859-1'), parse_parts(RDDATA, 0, [])))
                    
                ANSWER_SECTION_STARTS = ANSWER_SECTION_STARTS + 24 + (RDLENGTH * 2)

            try: ATYPE
            except NameError: None
            else:  
                res.append("# ANSWER " + str(ANSWER_COUNT + 1))
                res.append("QDCOUNT: " + str(int(QDCOUNT, 16)))
                res.append("ANCOUNT: " + str(int(ANCOUNT, 16)))
                res.append("NSCOUNT: " + str(int(NSCOUNT, 16)))
                res.append("ARCOUNT: " + str(int(ARCOUNT, 16)))
                
                res.append("ANAME: " + ANAME)
                res.append("ATYPE: " + ATYPE + " (\"" + get_type(int(ATYPE, 16)) + "\")")
                res.append("ACLASS: " + ACLASS)
                
                res.append("\nTTL: " + str(TTL))
                res.append("RDLENGTH: " + str(RDLENGTH))
                res.append("RDDATA: " + RDDATA)
                res.append("RDDATA decoded (result): " + RDDATA_decoded + "\n")

    return "\n".join(res)

def get_type(type):
    types = [
        "ERROR", # type 0 does not exist
        "A",
        "NS",
        "MD",
        "MF",
        "CNAME",
        "SOA",
        "MB",
        "MG",
        "MR",
        "NULL",
        "WKS",
        "PTS",
        "HINFO",
        "MINFO",
        "MX",
        "TXT"
    ]

    return "{:04x}".format(types.index(type)) if isinstance(type, str) else types[type]

def parse_parts(message, start, parts):
    part_start = start + 2
    part_len = message[start:part_start]
    
    if len(part_len) == 0:
        return parts
    
    part_end = part_start + (int(part_len, 16) * 2)
    parts.append(message[part_start:part_end])

    if message[part_end:part_end + 2] == "00" or part_end > len(message):
        return parts
    else:
        return parse_parts(message, part_end, parts)


# url = input("Enter the name Address : ")
csv_files = open("urlResponse.csv", "w")

with open('url.txt', 'r') as csv_file:
    csv_reader = csv.reader(csv_file)
    for url in csv_reader:
        print(url)
        message = build_message("A", url[0]) 
        print("Request:\n" + message)
        print("\nRequest (decoded):" + decode_message(message))

        response = send_udp_message(message, "1.1.1.1", 53)
        print("\nResponse:\n" + response)
        print("\nResponse (decoded):" + decode_message(response))
        csv_files.write(response)
csv_files.close()