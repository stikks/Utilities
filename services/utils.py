import re
import json
from unicodedata import normalize
from datetime import datetime, date, timedelta
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

from pygeocoder import Geocoder

_slugify_punct_re = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')


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

    result = []
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
    :param dest: destination dict to write to

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
        return (result.longitude, result.latitude)
    except Exception as e:
        print(e)
        return None
