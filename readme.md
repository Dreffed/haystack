# Haystack Web Collector Suite  

__This suite is undergoing conversion to Python 3+__ 

Haystack is a tool used to harvest data from a variety of web sites and will push the data to an underlying database (Maria DB)
This is an initial working program started in 2009, a newer version called Peregrin is under development.

## Getting Started

To use Haystack
* create a db schema (schema/peregrin.mwb)
* Each Module can be run as a standalone instance, see self runner code in wach module

### Prerequisites

Mariadb or MySQL installed and a database called Peregrin setup
Imstall the following modules:
* pip install configparser
* pip install mysqlclient

_ some modules use other libraries, please review includes imports in each module _

## Authors

* **David Gloyn-Cox** - *Initial work* - [Dreffed](https://github.com/Dreffed)

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

* This program was written to scratch an itch I had while looking for gainful employment
