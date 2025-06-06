import logging

with open("alchemy.log", "w", encoding="utf-8"):
    pass
logger = logging.getLogger(__name__)
logging.basicConfig(
    filename="alchemy.log",
    format="%(levelname)s\t%(asctime)s\t%(message)s",
    level=logging.DEBUG,
)


# def log_class(cls: object):
#     def log_fun(fun):
#         def inner(*args, **kwargs):
#             logger.debug(
#                 "Calling %s.%s with arguments: %s and keyword arguments: %s",
#                 cls.__name__,
#                 fun.__name__,
#                 args,
#                 kwargs,
#             )
#             res = fun(*args, **kwargs)

#             logger.debug("Called %s with result: %s", fun.__name__, res)
#             return res

#         return inner

#     for name, attribute in cls.__dict__.items():
#         if callable(attribute) and "__" not in name:
#             setattr(cls, name, log_fun(attribute))

#     return cls
