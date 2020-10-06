An App for Moving Django Models between apps
================================================

Django migrations are a blessing.
But they present a specific challenge when refactoring requires a model be moved to a different app,
while maintaining production data.

Problem:
--------
You are re-factoring a (legacy) app and need to move a Model class to a different app.
You need to ensure (production) data in the DB is maintained and available to the destination app.
You want the DB table names to be consistent with the code's new app-structure.
Issue: django provides no out-of-the-box solution to manage the schema + data migrations neccessary to accomplish this.

Purpose:
--------
  1. document some of the strategies I encountered while researching this problem;
  2. demonstrate the (elegant?) solution I am now successfully using

Strategies
----------
Many strategies have been devised, here are some of the more reasonable ones I encountered:

 A) Migration Reset (Nuclear option)

    * Exemplified by : https://simpleisbetterthancomplex.com/tutorial/2016/07/26/how-to-reset-migrations.html
    * Basic Idea:
        - use ``--fake`` migrations to update migration state in origin and destination apps
        - hard-code ``db_table`` in moved model(s), or rename table(s) of moved model(s) to match django defaults
    * Pros: clean migration history; fairly simple; no custom SQL or data migrations
    * Cons: carefully orchastrated deployment script;  mistakes may cause data loss; not trivial to reproduce or reverse
    * *Use it?* if you are moving ALL the models to NEW apps; reproducibiility and reversiblity not important

 B) "Neutered Migrations"

    * Exemplified by : https://wellfire.co/this-old-pony/refactoring-django-apps--a-better-way-of-moving-models--this-old-pony-33/
    * Basic Idea:
        - employ a "Neutered Migration" to update model history in migrations file without actually changing DB
    * Pros: reproducible; flexible; no "fake" migrations; maintains migration history
    * Cons: post-hoc clean-up,
            requires origin app and its migrations are left in place, then eventually moved to dest model and squashed
    * *Use it?*  **Yes** but read on!!

 C) "SeparateDatabaseAndState with AlterModelTable"

    * Exemplified by : https://realpython.com/move-django-model/#the-django-way-rename-the-table
    * Basic Idea:
        - perform code refactor and makemigrations for both origin and destination apps, as normal
        - edit migrations and substitute SeparateDatabaseAndState for migration operations
        - use AlterModelTable
    * Pros: reproducible; reversible, flexible; no "fake" migrations; clean migration history; no post-hoc cleanup
    * Cons: hard-to-remember, hand-edited migration code required.
    * *Use it?*  **Absolutely!** but read on!!

An App to do That
-----------------

The strategy documented below is based on strategy (C), but packaged as a small django app to keep things simple.

    * Pros: reproducible and reversible, clean migration history; safe*; little to no post-hoc clean up
    * Cons: migration history for model not retained; need to hand-edit one migration file;
    * *Use it?*  when you want a clean migration history and to remove origin migrations completely

* Note by "safe" I mean that even if you forget to use the ``--fake_initial`` flag during a migration,
    no data will be lost;  worst that happens is an error when migrations run indicating table already exists.

Model Migration Steps:
______________________

    **Best Practice**: ensure all migrations are up-to-date in both the origin and destination app
        ``> django-admin makemigrations --dry-run origin destination``

    1. refactor app code, moving model(s) from origin app to destination app (using normal re-factoring process)

    2. makemigrations for both origin and destination apps (DeleteModel in origin and CreateModel in destination)
        ``> django-admin makemigrations origin destination``

    3. edit the new origin app migration script and replace the ``DeleteModel`` migration operation with
        `move_model.operations.MoveModelOut` -- simply change the name of the operation and
        add a 'table' argument to provide the destination table name -- {applabel}_{modelname} by default.

        This custom operation applies ``DeleteModel`` to the migration state, but uses an ``AlterModelTable``
        operation to rename the DB table rather than deleting it.

        see origin.migrations.0003_delete_modeltomove

    4. edit the destination app migration script and replace the ``CreateModel`` migration operation with
        `move_model.operations.MoveModelIn` (literally simply replace name of operation).

        This custom operation applies ``CreateModel`` to the migration state, but prevents any DB operation,
        since the table, along with all its data, already exists!

        see destination.migrations.0001_initial

    5. Deploy the migrations::

        > django-admin migrate

    Have a beer.

Tutorial
--------
For a more detailed explanation and tutoral, see: https://realpython.com/move-django-model/#the-django-way-rename-the-table
This app simply packages up the migration operations to make them easier to re-write.


Running this demo:
______________________

This project contains an origin and destination app with all the migration scripts required to
 a) create the model in the origin
 b) migrate it to the destination

To walk through the demo, start by creating the model on the ``origin`` app::

    > django-admin migrate origin 0002_modeltomove_new_field

Now you can run some tests with the origin model::

    >>> from origin.models import ModelToMove
    >>> ModelToMove.objects.create(title='New Item')
    >>> ...

The model code re-factor is already done (see ``destination.models``).
Run remainder of migrations to complete the DB refactor::

    > django-admin migrate

(renames DB table and updates migration state history to DeleteModel in origin app, and CreateModel in destination app)

Now you can run some tests with the migrated model::

    >>> from destination.models import ModelToMove
    >>> print(ModelToMove.objects.filter(title='New Item').first())
    >>> ...

Voila.


Kudos
-----

I owe a debt of gratitude to bennylope for his marvelous NeuteredMigrations idea that got me started:
https://gist.github.com/bennylope/07f0860aeb3ca2eb66656cfdf2396854#file-migrations-py

and another to Haki Benita over at _RealPython: https://realpython.com/ for a clear tutorial on how to apply
``SeparateDatabaseAndState`` and ``AlterModelTable`` migration operations to achieve this end

Gotta love open source!
