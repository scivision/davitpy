# -*- coding: utf-8 -*-
# Copyright (C) 2012  VT SuperDARN Lab
# Full license can be found in LICENSE.txt
"""Ray tracing for SuperDARN (raydarn)

This module wraps the ray-tracing coupled with IRI and IGRF

Modules
--------------------------------
raydarn.rt  interfacing run code
--------------------------------

"""
from __future__ import absolute_import
import logging

try: from .rt import *
except Exception as e:
    logging.exception(__file__ + ' -> models.raydarn.rt: ' + str(e))
