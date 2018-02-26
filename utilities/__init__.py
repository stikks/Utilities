from utilities.utils import *
from logging import handlers, INFO, Formatter, getLogger


class ObjectNotFoundException(Exception):
    """ This exception is thrown when an object is queried by ID and not retrieved """

    def __init__(self, klass, obj_id):
        message = "%s: Object not found with id: %s" % (klass.__name__, obj_id)
        self.data = {"name": "ObjectNotFoundException", "message": message}
        self.status = 404
        super(ObjectNotFoundException, self).__init__(message)


class ServiceLabs(object):

    @staticmethod
    def setup_log(log_name, log_file, level=INFO):
        """
        log messages to file
        :return:
        """
        logger = getLogger(log_name)
        logger.setLevel(level)
        if logger.handlers:
            logger.handlers = []
        log_format = Formatter(
            '%(asctime)s %(levelname)s: %(message)s '
            '[in %(pathname)s:%(lineno)d]'
        )
        handler_ = handlers.RotatingFileHandler(log_file, maxBytes=500 * 1024)
        handler_.setLevel(level)
        handler_.setFormatter(log_format)
        logger.addHandler(handler_)

        return logger

    @staticmethod
    def setup_handlers(log_name, handler_name, level):
        """
        log handlers for different log levels
        :param log_name: file name
        :param handler_name: logging level
        :param level
        :return:
        """
        log_format = Formatter(
            '%(asctime)s %(levelname)s: %(message)s '
            '[in %(pathname)s:%(lineno)d]'
        )
        handler_ = handlers.RotatingFileHandler("/var/log/%s/%s.log" % (log_name, handler_name), maxBytes=500 * 1024)
        handler_.setLevel(level)
        handler_.setFormatter(log_format)

        return handler_

    @classmethod
    def create_instance(cls, class_obj, db):
        """
        creates a service class instance for a model class
        :param class_obj:
        :param db:
        :return: model service class
        """
        class Base(object):

            @classmethod
            def create(cls, ignored=None, **kwargs):
                """
                creates a model object based on the service model class
                :param ignored:
                :param kwargs:
                :return: model object relating to klass
                """
                if not ignored:
                    ignored = ["id", "date_created", "last_updated"]

                _obj = class_obj()
                data = clean_kwargs(ignored, kwargs)
                obj = populate_obj(_obj, data)

                Base.conn.session.add(obj)
                # current_db_session = Base.conn.object_session(_obj)
                # print(current_db_session)
                # exit()
                # current_db_session.add(obj)

                try:
                    Base.conn.session.commit()
                    # current_db_session.commit()
                    return obj
                except:
                    Base.conn.session.rollback()
                    raise

            @classmethod
            def update(cls, obj_id, ignored=None, **kwargs):
                """
                update model object with id matching obj_id
                :param obj_id:
                :param ignored:
                :param kwargs:
                :return: model object
                """
                _obj = Base.query.get(obj_id)

                if not _obj:
                    raise ObjectNotFoundException(Base.model_class, obj_id)

                if not ignored:
                    ignored = ["id", "date_created", "last_updated"]

                data = clean_kwargs(ignored, kwargs)
                obj = populate_obj(_obj, data)
                Base.conn.session.merge(obj)
                # Base.conn.session.add(obj)
                # current_db_session = Base.conn.object_session(obj)
                # current_db_session.add(obj)

                try:
                    Base.conn.session.commit()
                    # current_db_session.commit()
                    return obj
                except:
                    # current_db_session.rollback()
                    Base.conn.session.rollback()
                    raise

            @classmethod
            def all(cls):
                """
                retrieve all model object matching model_class
                :return: object
                """
                result = Base.query.all()

                if not result:
                    raise Exception

                return result

            @classmethod
            def get(cls, obj_id):
                """
                retrieve model object with id matching obj_id
                :param obj_id:
                :return: object
                """
                obj = Base.query.get(obj_id)

                if not obj:
                    raise ObjectNotFoundException(Base.model_class, obj_id)

                return obj

            @classmethod
            def filter_by(cls, first_only=True, **kwargs):
                """
                query a model using parameters in kwargs
                :param kwargs:
                :return:
                """
                try:
                    query = Base.query.filter_by(**kwargs)
                    if not first_only:
                        return query.all()
                    return query.first()
                except:
                    return None if first_only else list()

            @classmethod
            def view_filter(cls, query, view_name=None, **kwargs):
                """
                query a model using parameters in kwargs
                :param kwargs:
                :return:
                """
                try:
                    view_func = getattr(cls, "%s_view_query" % view_name.lower(), None) if view_name else None
                    return view_func(query) if view_func else query

                except Exception as e:
                    print(e)
                    return Base.query

            @classmethod
            def delete(cls, obj_id):
                """
                delete model object with id matching obj_id
                :param obj_id:
                :return: True
                """
                obj = Base.query.get(obj_id)
                obj = Base.conn.session.merge(obj)

                if not obj:
                    raise ObjectNotFoundException(Base.model_class, obj_id)

                current_db_session = Base.conn.object_session(obj)
                current_db_session.delete(obj)

                try:
                    current_db_session.commit()
                    return {}
                except:
                    current_db_session.rollback()
                    raise

            @classmethod
            def get_by_ids(cls, ids=None):
                """
                return objects matching ids
                :param ids:
                :return:
                """
                if not ids:
                    ids = []

                objects = Base.query.filter(Base.model_class.id.in_(ids))

                return objects

            @classmethod
            def update_by_ids(cls, ids, ignored=None, **kwargs):
                """
                update objects matching ids
                :param ids:
                :return:
                """
                # clean kwargs
                data = clean_kwargs(ignored, kwargs)
                data = remove_invalid_attributes(Base.model_class(), data)

                try:
                    res = Base.query.filter(Base.model_class.id.in_(ids)).update(data, synchronize_session=False)
                    Base.conn.session.commit()
                    return res
                except:
                    Base.conn.session.rollback()
                    raise

            @classmethod
            def delete_by_ids(cls, ids=None):
                """
                delete objects matching ids
                :param ids:
                :return:
                """
                if not ids:
                    ids = []

                for obj in Base.query.filter(Base.model_class.id.in_(ids)):
                    current_db_session = Base.conn.object_session(obj)
                    current_db_session.delete(obj)

                    try:
                        current_db_session.commit()
                        return obj
                    except:
                        current_db_session.rollback()
                        raise
                return True

        Base.model_class = class_obj
        Base.conn = db
        Base.query = Base.model_class.query

        return Base
