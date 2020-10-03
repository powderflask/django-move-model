A Strategy for Moving Django Models between apps
================================================

Django migrations are a blessing.
But they present a specific challenge when refactoring requires a model be moved to a different app,
while maintaining production data.

Problem:
--------
You are re-factoring a (legacy) app and need to move a Model class to a different app.
You need to ensure (production) data in the DB is maintained and available to the destination app.
Issue: django provides no built-in mechanism to manage the schema + data migrations neccessary to accomplish this.

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
        - run a fake reverse migration on origin app:
            ``> django-admin migrate --fake origin_app zero``
        - re-factor origin app code and remove all migration files
        - set explicit table names on model.Meta OR rename db tables to use django default (applabel_modelname)
        - make and run fake intial migration on desitnation app:
            ``> django-admin makemigrations dest_app``

            ``> django-admin migrate --fake-initial dest_app``
    * Pros: clean migration history; easy to undestand; no custom SQL or data migrations
    * Cons: carefully orchastrated deployment script;  mistakes may cause data loss
    * *Use it?* when you are moving ALL the models from origin to NEW apps

 B) Data Migration:

    * Basic Idea:
        - re-factor origin app code leaving origin app in-place
        - run initial migration:
            ``> django-admin makemigrations dest_app``

            ``> django-admin migrate dest_app``
        - add custom data migration to copy data from old table to new one with reverse doing nothing
        - run the migration:   ``> django-admin migrate dest_app``
        - once prod. migration complete, remove old app, delete orig. tables, reverse data migration (null), and remove it
    * Pros: clean migration history; easy to undestand;
    * Cons: not re-producible / will not work when tests try to run migrations; post-hoc clean-up required
    * *Use it?*  **Don't**

 C) SQL Monkey-patching:

    * Basic Idea:
        - refactor app code, moving all models and migrations together to new package
        - develop SQL script to
            1) rename model table(s) to use django default (applabel_modelname)
            2) modify app name in migrations table
    * Pros: simple; maintains migration history
    * Cons: custom SQL script required; only works when all models are moving together to new app
    * *Use it?*  **Don't**

 D) "Neutered Migrations"

    * Exemplified by : https://wellfire.co/this-old-pony/refactoring-django-apps--a-better-way-of-moving-models--this-old-pony-33/
    * Basic Idea:
        - employ a "Neutered Migration" to update model history in migrations file without actually changing DB
    * Pros: reproducible; flexible; no "fake" migrations; maintains migration history
    * Cons: post-hoc clean-up:
            requires origin app and its migrations are left in place, then eventually moved to dest model and squashed
    * *Use it?*  **Yes** but read on!!


Hybrid Strategy
-----------------

The strategy documented below is a hybrid of strategies (D) and (C)
(Neutered DeleteModel w/ fake CreateModel + SQL migration to rename model's DB table).

I owe a debt of gratitude to bennylope for his marvelous NeuteredMigrations code:
https://gist.github.com/bennylope/07f0860aeb3ca2eb66656cfdf2396854#file-migrations-py

    * Pros: reproducible and reversible, clean migration history; safe*; little to no post-hoc clean up
    * Cons: loses migration history for model; need to hand-edit one migration file;

* Note: by "safe" I mean that even if you forget to use the ``--fake_initial`` flag during a migration,
    no date will be lost;  worst that happens is an error message indicating table already exists.

Model Migration Steps:
______________________

    **IMPORTANT**: ensure all migrations are up-to-date in both the origin and destination app
        ``> django-admin makemigrations --dry-run origin destination``

    1. refactor app code, moving model(s) from origin app to destination app (using normal re-factoring process)

    2. makemigrations for both origin and destination apps (DeleteModel in origin and CreateModel in destination)
        ``> django-admin makemigrations origin destination``

    3. edit the new origin app migration script to 'monkey-patch' the db table:
        i) modify the migration to make it a "NeuteredMigration"::

            from neutered_migration import migrations

            class Migration(migrations.NeuteredMigration):
                ...

        ii) surreptitiously rename DB table to default in destination app

           Insert this SQL migration to re-name the db table AHEAD of the DeleteModel migration::

            from django.db.migrations.operations import RunSQL

            RunSQL(
                sql = [
                    "ALTER TABLE {origin} RENAME TO {destination};".format(
                    origin=orgin_table_name, destination=destination_table_name),
                ],
                reverse_sql=[
                    "ALTER TABLE {destination} RENAME TO {origin};".format(
                        origin=orgin_table_name, destination=destination_table_name),
                ]
            )

        see origin.migrations.0003_delete_modeltomove
            destination.migrations.0001_initial

    - Deploy migrations (sequence is CRITICAL)::

        > migrate origin  # NeuteredMigration prevents error due to table not existing
        > migrate destination --fake-intial  # if you forget --fake-initial, fails with "table already exists"

    Have a beer.

    - once all models are migrated out of origin app, all its migrations can be deleted without issue


Running this demo:
______________________

This project contains an origin and destination app with all the migration scripts required to
 a) create the model in the origin
 b) migrate it to the destination

To walk through the demo, start by creating the model on the ``origin`` app::

    > django-admin migrate origin 0002_modeltomove_newfield

Now you can run some tests with the origin model::

    >>> from origin.models import ModelToMove
    >>> ModelToMove.objects.create(title='New Item')
    >>> ...

Do the model re-factor simply by commenting out ``origin.models.ModelToMove`` class definition.

Run migrations to accompany the refactor::

    > django-admin migatate origin
    > django-admin migrate destination --fake-initial


Renames DB table and records migrations history to DeleteModel in origin app, and CreateModel in destination app;

Now you can run some tests with the migrated model::

    >>> from destination.models import ModelToMove
    >>> print(ModelToMove.objects.filter(title='New Item').first())
    >>> ...

Voila.
