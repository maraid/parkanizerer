
# Parkanizerer

_A simple tool that books an office desk on [tidaro.com](https://www.tidaro.com) ([parkanizer.com](https://share.parkanizer.com/) before)._

Parkanizer only let's you book a desk 1 week ahead. 

### Default operation
Using crontab, this script will run on each weekday when you usually go to the office just after midnight and books the desk for a week later.

### Selected days operation
By filling the "days_of_week" array in the config.json file you can select the specific weekdays you wish to book. Keep in mind that monday is the 0th day. If his array is empty execution will fall back to the default operation.

__Your password will be stored as clear text.__ So make sure that you use one on parkanizer that isn't used elsewhere.

Don't forget to release your desk if you decide not to go to the office.

## Installation and Usage

1. Clone this repo
```bash
git clone git@github.com:maraid/parkanizerer.git
```
2. Either setup a virtualenv or use the global one. The project only uses the [requests](https://pypi.org/project/requests/) package.
```bash
python -m pip install -r requirements.txt
```

3. Setup your configuration by creating `config.json` based on [`config.json.example`](https://github.com/maraid/parkanizerer/blob/master/config.json.example). Log in to parkanizer and check the exact name of the zone and desk that you want to book.

4. Add entries to crontab that runs the script when you want to visit the office using `crontab -e`.

e.g:

```text
  1 0 * * 1 /path/to/parkanizerer/main.py &>> /path/to/parkanizerer/parkanizerer.log
```
This will run the script on each monday one minute after midnight and it'll book the selected desk for the next week.

5. For windows installation create a shortcut to the parkanizerer.cmd file. Then copy the shortcut to the windows Startup folder. You can find this easily by pressing Win+R and typing "shell:startup".

## License

[MIT](https://choosealicense.com/licenses/mit/)
