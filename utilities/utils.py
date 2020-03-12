import re
import base64
import json
from unicodedata import normalize
from datetime import datetime, date
from email.utils import formatdate
from calendar import timegm
from user_agents import parse
import requests
import os
import string
import random
import phonenumbers
import hashlib
import uuid
import pyaes

import htmlmin
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
from PIL import Image as PImage

from pygeocoder import Geocoder


aes_secret_key = os.environ.get("AES_SECRET_KEY","")

class Payload(object):
    def __init__(self, **kwargs):
        self.__dict__ = kwargs


class DateJSONEncoder(json.JSONEncoder):
    """ JSON Encoder class to support date and time encoding """

    def default(self, obj):
        if isinstance(obj, datetime):
            return formatdate(timegm(obj.utctimetuple()), usegmt=True)

        if isinstance(obj, date):
            _obj = datetime.combine(obj, datetime.min.time())
            return formatdate(timegm(_obj.utctimetuple()), usegmt=True)

        return json.JSONEncoder.default(self, obj)


def expand_errors(data):
    """ Cleans up the error data of forms to enable proper json serialization """
    res = {}
    for k, v in data.items():
        tmp = []
        for x in v:
            tmp.append(str(x))
        res[k] = tmp

    return res


def slugify(text, delim=u'-'):
    """
    Generates an ASCII-only slug.

    :param text: The string/text to be slugified
    :param: delim: the separator between words.

    :returns: slugified text
    :rtype: unicode
    """

    result = list()
    _slugify_punct_re = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')
    for word in _slugify_punct_re.split(text.lower()):
        # ensured the unicode(word) because str broke the code
        word = normalize('NFKD', unicode(word)).encode('ascii', 'ignore')
        if word:
            result.append(word)
    return unicode(delim.join(result))


def normalize_text(text):

    """
    Generates an ASCII-only text
    :rtype: str
    """
    if text:
        result = []
        for word in text:
            # ensured the unicode(word) because str broke the code
            word = normalize('NFKD', unicode(word)).encode('ascii', 'ignore')
            if word:
                result.append(word)
        return unicode(''.join(result))


def clean_kwargs(ignored_keys, data):
    """
    Removes the ignored_keys from the data sent

    :param ignored_keys: keys to remove from the data (list or tuple)
    :param data: data to be cleaned (dict)

    returns: cleaned data
    rtype: dict
    """

    for key in ignored_keys:
        data.pop(key, None)

    return data


def populate_obj(obj, data):
    """
    Populates an object with the data passed to it

    :param obj: Object to be populated
    :param data: The data to populate it with (dict)

    :returns: obj populated with data
    :rtype: obj.__class__

    """
    for name, value in data.items():
        if hasattr(obj, name):
            setattr(obj, name, value)

    return obj


def remove_invalid_attributes(obj, data):
    """ remove the attributes of a dictionary that do not belong in an object """
    _data = {}
    for name, value in data.items():
        if hasattr(obj, name):
            _data[name] = value

    return _data


def validate_data_keys(data, keys):
    """
    Check the data dictionary that all the keys are present within it
    """
    for k in keys:
        if not data.has_key(k):
            raise Exception("Invalid data. All required parameters need to be present. Missing Key: [%s]" % k)

    return data


def copy_dict(source, destination):
    """
    Populates a destination dictionary with the values from the source

    :param source: source dict to read from
    :param destination: destination dict to write to

    :returns: destination
    :rtype: dict

    """
    for name, value in source.items():
        destination[name] = value
    return destination


def remove_empty_keys(data):
    """ removes None value keys from the list dict """
    res = {}

    for key, value in data.items():
        if value is not None:
            res[key] = value

    return res


def detect_user_agent(ua_string):
    """
    Detects what kind of device is being used to access the server
    based on the user agent

    :param ua_string: The user agent string to parse

    :returns: user agent object
    """

    ua = parse(ua_string)

    return ua


def prepare_errors(errors):
    _errors = {}
    for k, v in errors.items():
        _res = [str(z) for z in v]
        _errors[str(k)] = _res

    return _errors


def detect_user_device(ua_string):
    """ returns which device is used in reaching the application. 'm' for mobile, 'd' for desktop and 't' for tablet """

    ua = detect_user_agent(ua_string)

    device = "d"

    if ua.is_tablet:
        device = "t"

    if ua.is_mobile:
        device = "m"

    if ua.is_pc:
        device = "d"

    return device


def download_file(url, dest, filename):
    """
    Downloads a file from a url into a given destination
    and returns the location when it's done

    :param url: url to downlaod from
    :param dest: destination folder
    :param filename: filename to save the downloaded file as

    """

    r = requests.get(url)
    path = os.path.join(dest, filename)
    with open(path) as doc:
        doc.write(r.content)
    doc.close()
    return path


def clean_ascii(raw):
    """
    Removes ascii characters from the data sent

    :param raw: data to be cleaned (dict)

    returns: cleaned data
    rtype: string
    """
    if type(raw) in [str,list]:
        clean = filter(lambda x: x in string.printable, raw)
        if len(clean) > 0:
            clean = clean.replace("&"," And ").replace("'s","").replace("----","-").replace("---","-").replace("--","-").replace("/","").replace("(","").replace(")","").replace("\\","").replace("%","").replace("!","")

            clean.encode('ascii',errors='ignore')
    else:
        clean = raw

    return clean


def build_page_url(path, data, p):
    args=""
    for k in data:
        if k=="page":
            args=args+"&page"+"="+str(p)
        else:
            args=args+"&"+str(k)+"="+str(data[k])

    return str(path)+"?"+str(args)


def id_generator(size=10, chars=string.ascii_letters+string.digits):
    """
    utility function to generate random identification numbers
    """
    return ''.join(random.choice(chars) for x in range(size)).upper()


def token_generator(size=8, chars=string.digits):
    """
    utility function to generate random identification numbers
    """
    return ''.join(random.choice(chars) for x in range(size))


def generate_uuid():
    return uuid.uuid4().hex


def number_format(value):
    return "{:,.2f}".format(float(value))


def is_list(value):
    return isinstance(value, (list, tuple))


def check_image_size(src, dimensions=(200, 200)):
    """ Check's image dimensions """
    img = PImage.open(src)
    width, height = img.size
    d_width, d_height = dimensions

    if int(width) == int(d_width) and int(height) == int(d_height):
        return True
    else:
        return False


def md5_hash(value):
    """ create the md5 hash of the string value """
    return hashlib.md5(value).hexdigest()


def join_list(value, key):
    """ Iterate through a list and retrieve the keys from it """
    return ", ".join([getattr(x, key, "") for x in value])


def clean_phone(number, code):
    _number = code + str(number)
    return _number


def clean_phone_number(number, code):
    num = []
    chars = ['or', 'and', '/', ',']

    for char in chars:
        if char in number:

            number = number.replace(char, "").strip().split()

            count = 0

            _num = []

            while count < len(number):
                nos = number[count]
                nos = filter(lambda x: x.isdigit(), nos)

                if nos.startswith('234'):
                    nos = nos[3:]

                action = clean_phone(int(nos), code)
                _num.append(action)
                count += 1

            return _num

    number = filter(lambda x: x.isdigit(), number)

    if number.startswith('234'):
        number = number[3:]

    _number = clean_phone(int(number), code)
    num.append(_number)

    return num


def format_phone_numbers(raw_numbers, code):
    """
    Properly formats a list or string of phone numbers into the country code

    :param raw_numbers: Phone number to parse and format
    :param code: country code to utilize
    :return: properly formatted phone number or None
    """

    # Convert list or tuple to string if passed
    if isinstance(raw_numbers, (list, tuple)):
        raw_numbers = ','.join(raw_numbers)

    numbers = []
    for n in raw_numbers.replace("or", ","). \
            replace("\n", ","). \
            replace(".", ","). \
            replace("and", ","). \
            replace(";", ","). \
            replace("/", ",").split(","):
        if len(n) > 0:
            try:
                _n = phonenumbers.parse(n, code)
                if _n and phonenumbers.is_valid_number(_n):
                    cc = _n.country_code
                    nn = _n.national_number
                    num = str(cc) + str(nn)
                    numbers.append(num)
            except Exception, e:
                pass

    return numbers


def generate_code(prefix, length):
    """
    returns alnum mashed up with prefix
    :param prefix:
    :param length:
    :return:
    """
    suffix = id_generator(length)
    return '{}-{}'.format(prefix, suffix).upper()


def compute_lat_lng(address):
    try:
        result = Geocoder.geocode(address)
        return getattr(result, 'longitude'), getattr(result, 'result.latitude')
    except Exception as e:
        print(e)
        return None


def check_extension(filename, extensions=("jpg", "jpeg", "png", "gif",)):
    """ Checks if the filename contains any of the specified extensions """

    bits = filename.split(".")
    bits.reverse()

    ext = bits[0].lower()

    return ext in extensions


def encrypt_3des(des_key, text):
    """
        Encrypt the specified value using the 3DES symmetric encryption algorithm
        :param des_key: encryption key
        :param text: parameter to encrypt
        :returns cipher_text: 3DES encrypted values
    """

    padder = padding.PKCS7(algorithms.TripleDES.block_size).padder()
    padded_text = padder.update(text) + padder.finalize()

    cipher = Cipher(algorithms.TripleDES(des_key), mode=modes.ECB(), backend=default_backend())
    encryptor = cipher.encryptor()
    cipher_text = encryptor.update(padded_text) + encryptor.finalize()

    return cipher_text


def decrypt_3des(des_key, cipher_text):
    """
        Decrypt the specified value using the 3DES symmetric decryption algorithm
        :param cipher_text: parameter to decrypt
        :param des_key: decryption key
        :returns u: plain text value
    """

    cipher = Cipher(algorithms.TripleDES(des_key), modes.ECB(), backend=default_backend())
    decryptor = cipher.decryptor()
    padded_text = decryptor.update(cipher_text) + decryptor.finalize()

    unpadder = padding.PKCS7(algorithms.TripleDES.block_size).unpadder()
    text = unpadder.update(padded_text) + unpadder.finalize()

    return text


def encrypt_data(des_key, data):
    """ encrypt the data sent in. Will return the 3des version of the dictionary """

    print json.dumps(data, indent=2)
    des_key = build_3des_key(des_key)
    encrypted_data = dict()

    for k, v in data.items():
        encrypted_data[k] = base64.b64encode(encrypt_3des(des_key, str(v)))

    return encrypted_data


def decrypt_data(des_key, data):
    """ decrypt the data sent in. Will return the plain version of the dictionary """

    print json.dumps(data, indent=2)
    des_key = build_3des_key(des_key)
    decrypted_data = dict()

    for k, v in data.items():
        decrypted_data[k] = decrypt_3des(des_key, base64.b64decode(str(v)))

    return decrypted_data


def build_3des_key(key):
    """ build the key for 3des using md5 digest"""

    m = hashlib.md5()
    m.update(key)
    des_key = m.digest()

    return des_key


def build_aes_key(key):
    """build an aes key of 16/24/32bytes, defaults to 16byte"""

    m = hashlib.md5()
    m.update(key)
    aes_key = m.hexdigest()

    return aes_key


def encrypt_aes(aes_key, text):
    """
        Encrypt the specified value using the 3DES symmetric encryption algorithm
        :param aes_key: encryption key
        :param text: parameter to encrypt
        :returns cipher_text: AES encrypted values
    """

    cipher = Cipher(algorithms.AES(aes_key), mode=modes.CTR(nonce=''), backend=default_backend())
    encryptor = cipher.encryptor()
    cipher_text = encryptor.update(text) + encryptor.finalize()

    return cipher_text


def encrypt_pyaes(aes_key, text):
    """encrypt ciphertext using ctr mode of the pyaes library"""

    aes = pyaes.AESModeOfOperationCTR(aes_key)
    ciphertext = aes.encrypt(text)

    return ciphertext


def decrypt_pyaes(aes_key, text):
    """decrypt ciphertext using ctr mode of the pyaes library"""

    aes = pyaes.AESModeOfOperationCTR(aes_key)
    plaintext = aes.decrypt(text)

    return plaintext


def encrypt_data_pyaes(key, data):
    """ encrypt the data sent in. Will return the aes version of the dictionary """

    # print json.dumps(data, indent=2)
    aes_key = build_aes_key(key)
    # print aes_key, 'enc key'
    encrypted_data = dict()

    for k, v in data.items():
        encrypted_data[k] = base64.b64encode(encrypt_pyaes(aes_key, str(v)))

    return encrypted_data


def decrypt_data_pyaes(key, data):
    """ decrypt the data sent in. Will return the plain version of the dictionary """

    print json.dumps(data, indent=2)
    aes_key = build_aes_key(key)
    print aes_key, 'dec key'
    decrypted_data = dict()

    for k, v in data.items():
        decrypted_data[k] = decrypt_pyaes(aes_key, base64.b64decode(str(v)))

    return decrypted_data


def dict_update(dic, data):
    """

    :param dic: the dictionary to be updated
    :param data: the data to use to update
    :return: dict
    """

    dic.update(data)
    return json.dumps(dic)


class ObjectPayload(object):
    def __init__(self, d):
        for a, b in d.items():
            if isinstance(b, (list, tuple)):
                setattr(self, a, [ObjectPayload(x) if isinstance(x, dict) else x for x in b])
            else:
                setattr(self, a, ObjectPayload(b) if isinstance(b, dict) else b)


def encrypt_form(enc_key, form, form_class):

    data = encrypt_data_pyaes(enc_key, form.data)
    new_obj = ObjectPayload(data)
    form = form_class(obj=new_obj)

    return form.data


def encrypt_dict_to_string(**data):
    string_data = json.dumps(data)
    aes_key = build_aes_key(aes_secret_key)
    aes = pyaes.AESModeOfOperationCTR(aes_key)
    cipher_text = aes.encrypt(string_data)

    return base64.b64encode(cipher_text)


def decrypt_string_to_dict(cipher_text):
    aes_key = build_aes_key(aes_secret_key)
    aes = pyaes.AESModeOfOperationCTR(aes_key)
    string_data = aes.decrypt(base64.b64decode(cipher_text))

    data = json.loads(string_data)

    return data


def render_domain_template(name, **kwargs):
    from flask import render_template
    template_name = name

    _html = render_template(template_name, **kwargs)

    return htmlmin.minify(_html, remove_empty_space=True, remove_comments=True)


def random_string(size=16, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))
