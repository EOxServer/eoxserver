python3 manage.py coveragetype import  autotest/data/SCL/scl_coverage_type.json
python3 manage.py producttype create SCL -c SCL
python3 manage.py browsetype create SCL SCL --grey scl

python3 manage.py coveragetype import

python3 manage.py rasterstyle import ./autotest/data/SCL/scl.sld --rename S2B_30UUG_20221226_0_L2A_scl SCL

python3 manage.py rasterstyle link SCL SCL SCL color

python3 manage.py product register -i S2B_30UUG_20221226_0_L2A -t SCL --footprint "POLYGON ((-6.1994886 55.9041676, -6.1207799 54.9190265, -4.4083987 54.9509423, -4.4439779 55.9372733, -6.1994886 55.9041676))" --replace
python3 manage.py coverage register -t SCL -r -d autotest/data/SCL/scl_small.tif --footprint-from-extent -i S2B_30UUG_20221226_0_L2A_scl -p S2B_30UUG_20221226_0_L2A

python3 manage.py visibility S2B_30UUG_20221226_0_L2A --wms
