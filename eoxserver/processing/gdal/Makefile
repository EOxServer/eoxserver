CC= gcc
LD= gcc
LD_SHARED = $(LD) -shared 

INCLUDES= -I "/usr/include/" -I "/usr/include/gdal/"
CCFLAGS= -c -g -Wall -fPIC $(INCLUDES)

LIBS= -lgdal1.7.0

OBJS= eoxs.o

EXE_LIST= eoxs

# --------------------------------------------

all: $(EXE_LIST) clean

%.o: %.c
	$(CC) $< $(CCFLAGS) -o $@

eoxs: $(OBJS)
	$(LD_SHARED) -Wl,-soname,eoxs.so -o eoxs.so $(OBJS) $(LIBS) 

clean:
	rm *.o

