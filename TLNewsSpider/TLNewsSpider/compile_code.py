# -*- coding:utf-8 -*-
# Author: devcm

'''
使用: python compile_code.py build
'''
import setuptools
from distutils.core import setup
from Cython.Build import cythonize
import os


def scan_folder(input_folder):

    file_list = []

    for f in os.listdir(input_folder):
        f_name = os.path.abspath(input_folder + "/" + f)
        if not os.path.isfile(f_name):
            file_list = file_list + scan_folder(f_name)
        else:
            if f.endswith(".py"):
                file_list.append(f_name)

    return file_list


def build_cython(file_paths):

    setup(
        ext_modules = cythonize(file_list, language_level=2)
    )
    for fipy in file_list:
        if fipy.endswith(".py"):
            os.remove(fipy.replace(".py", ".c"))


need_build_moduel = ['spiders']

for moduel in  need_build_moduel:

    file_list = scan_folder(moduel)

    build_cython(file_list)

