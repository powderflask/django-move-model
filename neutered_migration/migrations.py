# -*- coding: utf-8 -*-

# Copyright (c) 2018, Ben Lopatin
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
Article: https://wellfire.co/this-old-pony/refactoring-django-apps--a-better-way-of-moving-models--this-old-pony-33/
Code: https://gist.github.com/bennylope/07f0860aeb3ca2eb66656cfdf2396854#file-migrations-py

Complete set of neutered migration operations
The classes herein can be substituted, manually, for Django's migration operation
classes in migration files to prevent execution of migrations.
"""

import sys
from django.db import migrations
from django.db.migrations.operations import base

# List of operations to NOT be Neutered (doesn't really make sense to neuter these, so prevent likely accidental uses)
nonneutered_operations =[
    migrations.operations.RunSQL, migrations.operations.RunPython, migrations.operations.SeparateDatabaseAndState,
]

# Grab all Operations defined in django.db.migrations (except for excluded ones)
operation_classes = [
    op for op in migrations.operations.__dict__.values()
    if type(op) is type and issubclass(op, migrations.operations.base.Operation) and op not in nonneutered_operations
]


# Validation Step to ensure we are very clear about which operations are being neutered.
operation_class_names = [
    'AddField', 'AlterField', 'RemoveField', 'RenameField', 'AddConstraint', 'AddIndex', 'AlterIndexTogether',
    'AlterModelManagers', 'AlterModelOptions', 'AlterModelTable', 'AlterOrderWithRespectTo',
    'AlterUniqueTogether', 'CreateModel', 'DeleteModel', 'RemoveConstraint', 'RemoveIndex', 'RenameModel',
]
assert all(op.__name__ in operation_class_names for op in operation_classes)


def factory(base):
    class NeuteredOperation(base):
        """
        Migrations operation that does not modify the database
        """

        def database_forwards(self, app_label, schema_editor, from_state, to_state):
            """Make no forwards changes of state in the database"""

        def database_backwards(self, app_label, schema_editor, from_state, to_state):
            """Make no backwards changes of state in the database"""

    NeuteredOperation.__name__ = '{}'.format(base.__name__)
    NeuteredOperation.__doc__ = '(Neutered) {}'.format(base.__doc__)

    return NeuteredOperation


class NeuteredMigration(migrations.Migration):
    # A drop-in replacement for django.db.migrations.Migration to clearly document that a Migration is Neutered.
    pass


# Add all the Neutered Operations to this module
neutered_module = sys.modules[__name__]

for operation in operation_classes:
    neutered_operation = factory(operation)
    setattr(neutered_module, neutered_operation.__name__, neutered_operation)
