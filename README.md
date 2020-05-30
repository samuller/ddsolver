# Setup

## Virtualenv

Setup a virtualenv (optional, but recommended):

    virtualenv -p python3 .env
    . .env/bin/activate

Then install required modules:

    pip install -r requirements.txt

## Django

Start Django's development server:

    python manage.py runserver

<!--
TODO:
~ support 8-connected and disjoint symbols
 * partially supported in transformations (hackish - only if there's a region in top-left corner)
- allow whole area to select symbol (even gaps)
- enlarge/pop-up symbols on hover
- allow transforming to higher resolution symbols by upscaling whole image 
  - keep aspect ratio
- make transformnation rules visible in UI
- allow custom transformation rules
- setup saving of transformation rules, notes and settings (localstorage/save file)
- combine all pages into single image? (automatically)

- add auto detection of:
 - symbols, based on connectivity
 - symbols, based on rectangular regions
 - symbols, based on separation
 - empty area (grids)

- include source images in repo
- include full explanation/guide in readme
- analyse source images for assumptions
 - consider "Principles of grouping", "Gestalt psychology", "Visual design elements and principles"
- add tests 
-->