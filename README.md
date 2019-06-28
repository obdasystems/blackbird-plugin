Blackbird Eddy Plugin
=====================

This repository contains the Eddy plugin for Blackbird,
an ontology-based relational database migration tool.

Packaging
---------

To create a redistributable `.zip` archive that can be installed in Eddy:

* Clone the repository:

```bash
 $ git clone https://github.com/obdasystems/blackbird-plugin
```

* Copy the Blackbird executable jar in the root folder of the project
  with name `blackbird.jar`.

* Run the following command from the project folder:

```bash
 $ ./build.sh package
```

At the end of the process the redistributable plugin `.zip` archive 
  can be found in the `build` folder.
  
Installing from the repository
------------------------------

To install the plugin from the git repository:

* Clone the repository:

```bash
 $ git clone https://github.com/obdasystems/blackbird-plugin
```

* Copy the Blackbird executable jar in the root folder of the project
  with name `blackbird.jar`.
  
* Run the following command from the project folder:
```bash
 $ ./build.sh install
```
