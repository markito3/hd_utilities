#!/bin/tcsh

set RUN = $1

mkdir calibration$RUN

# do walk correction
root -b -q "src/walk1.C+($RUN)"

# do mean time determination
./domeantime.csh $RUN &

set PID = $!

# calculate time differences
./dotimediff.csh $RUN

while ( `ps -p "$PID" | wc -l` > 1 )
  sleep 60
end

# calculate eff. speeds in paddles for both planes
root -b -q "src/tdlook.C($RUN,0)"
root -b -q "src/tdlook.C($RUN,1)"

# determined individual PMT offsets from mean time offsets and
# time difference offsets
root -b -q "src/consolidate.C($RUN)"

# option 10: get TOF TDC calibration for single ended paddles
root -b -q "src/dofitall.C+($RUN,10)"

# determine adc time offsets so that T_TDC - T_ADC will be peaked at zero.
root -b -q "src/doadctimeoffsets.C+($RUN)"


# determine attenuation length
#root -b -q "src/dofit.C($RUN)"