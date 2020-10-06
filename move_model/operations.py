# -*- coding: utf-8 -*-

# Copyright (c) 2020, Powderflask
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# Redistributions of source code must retain the above copyright notice, this
# list of conditions and the following disclaimer.  Redistributions in binary
# form must reproduce the above copyright notice, this list of conditions and the
# following disclaimer in the documentation and/or other materials provided with
# the distribution
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""
Based on:
Article: https://realpython.com/move-django-model/#the-django-way-rename-the-table

Complete set of move_model migration operations
The classes herein can be swapped, manually, for Django's DeleteMdodel and CreateModel migration operation
classes in migration files to Rename the DB table during migrations instead.
"""

from django.db import migrations
from django.db.migrations import operations


class MoveField(operations.SeparateDatabaseAndState):
    """ Drop-in replacement for RemoveFiel -- updates state but without touching DB table """
    def __init__(self, model_name, name, **kwargs):
        """
           Arguments as per RemoveField (i.e., from the django migration file made for the model moved to its new app)
        """
        super().__init__(
            state_operations=[
                operations.RemoveField(model_name=model_name, name=name, **kwargs),
            ],
            database_operations=[]
        )


class MoveModelOut(operations.SeparateDatabaseAndState):
    """ Near drop-in replacement for DeleteModel, but renames the DB table instead of deleting it """
    def __init__(self, name, table):
        """
            @:param name: name of model to be moved -- same as DeleteModel(name=...)
            @:param table: destination DB table name -- what to rename the db_table from this model
                    typically: {app_label}_{modelname} for the destination app where model is being moved to.
        """
        super().__init__(
            state_operations=[
                operations.DeleteModel(name=name),
            ],
            database_operations = [
                migrations.AlterModelTable(name=name, table=table,),
            ],
        )

class MoveModelIn(operations.SeparateDatabaseAndState):
    """ Drop-in replacement for CreateModel, but assumes the DB table already exists in DB """
    def __init__(self, name, fields, **kwargs):
        """
           Arguments as per CreateModel (i.e., from the django migration file made for the model moved to its new app)
        """
        super().__init__(
            state_operations=[
                migrations.CreateModel(name=name, fields=fields, **kwargs),
            ],
            database_operations = [], # Table must already exist, usually by preceding MoveModelOut operation.
        )
