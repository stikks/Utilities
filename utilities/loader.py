"""
loader.py

@Author: Olukunle Ogunmokun

Load objects from an external json document and populate an object or objects with the data

"""

import json
import utils
import os


def get_or_create(db, model, **kwargs):
    """ attempt to fetch an object that matches the parameters first or create it if not found"""
    instance = model.query.filter_by(**kwargs).first()

    if instance:
        return instance, False
    else:
        instance = utils.populate_obj(model(), kwargs)
        try:

            db.session.add(instance)
            db.session.commit()
            return instance, True
        except:
            db.session.rollback()
            raise


def load_class(module, class_name):
    """ Loads the class from a module by the class name"""
    klass = getattr(module, class_name, None)
    return klass


def append_children(db, module, obj, children=[]):
    """ Append the children to a parent object """

    for _data in children:
        class_name = _data.get("model", None)
        property_name = _data.get("property", None)
        objects = _data.get("objects", None)
        parent = _data.get("parent", None)
        klass = load_class(module, class_name)

        if klass and parent and property_name and objects:
            for _d in objects:
                _d[parent] = obj.id
                child, status = get_or_create(db, klass, **_d)
                getattr(obj, property_name).append(child)

        db.session.commit()


def load_data(module, db, filepath):
    """ Loads up a json file and converts the data inside to python objects """

    f = open(filepath)

    data = json.loads(f.read().encode("UTF-8"))

    # extract the information required
    class_name = data.get("model", None)
    objects = data.get("objects", [])

    klass = load_class(module, class_name)

    if klass:
        for _data in objects:
            # extract the children first then create the parent and append the children next
            children = _data.pop("children", [])
            obj, status = get_or_create(db, klass, **_data)
            append_children(db, module, obj, children)
            # print "Done"


def load_via_filepath(module, db, filepath, template_base_dir, extra_data={}):
    """ Loads up a json file and updates the data inside based on the content of the file """

    _file = open(filepath)

    data = json.loads(_file.read().encode("UTF-8"))

    objects = data.get("objects")
    class_name = data.get("model")

    base_path = os.path.join(template_base_dir, data.get("base_path"))
    klass = load_class(module, class_name)

    model_objects = []

    if klass:
        for element in objects:
            file_path = element.pop('file_path')

            for key, value in file_path.items():

                key_addr = os.path.join(base_path, value)
                # check if file exists
                if os.path.isfile(key_addr):
                    key_file = open(key_addr)
                    element[key] = key_file.read().encode('UTF-8')
                    element.update(extra_data)
            # extract the children first then create the parent and append the children next
            children = element.pop("children", [])
            obj, status = get_or_create(db, klass, **element)
            model_objects.append(obj)
            append_children(db, module, obj, children)

    return model_objects