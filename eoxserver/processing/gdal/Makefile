CC= gcc
LD= gcc
LD_SHARED = $(LD) -shared 

INCLUDES=`gdal-config --cflags`
CCFLAGS= -c -g -Wall -fPIC $(INCLUDES)

LIBS=`gdal-config --libs`

OBJS= reftools.o

EXE_LIST= reftools

# --------------------------------------------

all: $(EXE_LIST) clean

%.o: %.c
	$(CC) $< $(CCFLAGS) -o $@

reftools: $(OBJS)
	$(LD_SHARED) -Wl,-soname,_reftools.so -o _reftools.so $(OBJS) $(LIBS) 

clean:
	rm *.o

