from aiohttp.web import View
import os
import importlib
import logging
import app
import log

global_register_handler = list()


def import_all():
    handler_dir = os.path.dirname(app.__file__)
    dir_list = os.listdir(handler_dir)
    for directory in dir_list:
        if "__" not in directory:
            if os.path.isdir(handler_dir + "//" + directory):
                subdir = handler_dir + "//" + directory
                for real_subdir in os.listdir(subdir):
                    if "__" not in real_subdir and real_subdir.split(".")[-1] == "py":
                        module_path = ".".join((app.__name__, directory, real_subdir.split(".")[0]))
                        lib = importlib.import_module(module_path)
                        for each_dir in dir(lib):
                            if "__" not in each_dir:
                                element = getattr(lib, each_dir)
                                if element is not None and not isinstance(element, (int, dict, str, bool)) \
                                        and getattr(element, "__hash__") is not None and issubclass(element, View) and \
                                        id(element) != id(View):
                                    if element not in global_register_handler:
                                        global_register_handler.append(element)
            else:
                module_path = ".".join((app.__name__, directory.split(".")[0]))
                lib = importlib.import_module(module_path)
                for each_dir in dir(lib):
                    if "__" not in each_dir:
                        element = getattr(lib, each_dir)
                        if issubclass(element, View) and id(element) != id(View):
                            global_register_handler.append(element)


def setup_routes(application):
    log.init_log(os.getcwd() + "//log//log")
    import_all()
    for handler in global_register_handler:
        # handler_instance = handler()
        logging.info("Path %s add Handler %s" % (handler.path, str(handler)))
        application.router.add_route("*", handler.path, handler)
