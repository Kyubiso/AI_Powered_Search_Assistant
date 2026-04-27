# Conda Cheat Sheet (Quick Reference)

## Create / Delete Environment

* `conda create -n env_name python=3.10`
* `conda remove -n env_name --all`

## Activate / Deactivate

* `conda activate env_name`
* `conda deactivate`

## Install Packages

* `conda install package_name`
* `conda install -c conda-forge package_name`

## Remove Packages

* `conda remove package_name`

## List

* `conda list`                # packages in current env
* `conda env list`            # all environments

## Export / Import Environment

* `conda env export > env.yml`
* `conda env create -f env.yml`

## Update

* `conda update conda`
* `conda update --all`
