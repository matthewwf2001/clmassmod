#!/bin/bash -u

r=5

for snap in 124 141; do

    cat hst_siminput.list | awk '($1 !~ "#"){print}' | { 

	while read cluster zcluster ndensity beta core coresizeindex spt_xi; do 
		    
	    for center in xrayNONE xraymag szanalytic szmag; do
		
		for mc in c4 diemer15; do
		    
		    config=hstnoisebins-${mc}-r${r}-${center}-${cluster}-feb2016
		
		    echo $config >> ../run22bk11$snap
		
		    dir=/vol/euclid1/euclid1_1/dapple/bk11_lensing/snap$snap/intlength400/$config
		
		    if [ ! -e $dir ]; then
			mkdir $dir
		    fi
		    
		    cat overhead.py bk11.py hstnoiseprofile.py ${mc}.py linearprior.py scanpdf.py r${r}.py > $dir/config.py
		 
		    echo "targetz=$zcluster" >> $dir/config.py



		    if [ "$center" = "xrayNONE" ]; then
			cat core_none.py >> $dir/config.py
			echo "profilefile='/vol/euclid1/euclid1_raid1/dapple/mxxlsims/shearprofiles/${cluster}.szcenter.profile'" >> $dir/config.py		

		    elif [ "$center" = "xraymag" ]; then
			cat xraymagneticum.py >> $dir/config.py
			echo "profilefile='/vol/euclid1/euclid1_raid1/dapple/mxxlsims/shearprofiles/${cluster}.xraycenter.profile'" >> $dir/config.py		

		    elif [ "$center" = "szanalytic" ]; then
			cat szanalytic.py >> $dir/config.py
			cat core_${coresizeindex}.py >> $dir/config.py
			echo "szbeam=1.2" >> $dir/config.py
			echo "sz_xi=$spt_xi" >> $dir/config.py
			echo "profilefile='/vol/euclid1/euclid1_raid1/dapple/mxxlsims/shearprofiles/${cluster}.szcenter.profile'" >> $dir/config.py		

		    elif [ "$center" = "szmag" ]; then
			cat szmagneticum.py >> $dir/config.py
			cat core_${coresizeindex}.py >> $dir/config.py
			echo "profilefile='/vol/euclid1/euclid1_raid1/dapple/mxxlsims/shearprofiles/${cluster}.szcenter.profile'" >> $dir/config.py		
		    fi


		done
   		
	    done
	   	
	done
    
    }

done


binning=lineargaussbins12
shapenoise=0.25
r=9

for snap in 124 141; do

    cat megacam_siminput.list | awk '($1 !~ "#"){print}' | { 

	while read cluster zcluster ndensity beta core coresizeindex spt_xi; do 
		    
	    for center in xrayNONE xraymag szanalytic szmag; do
		
		for mc in c4 diemer15; do

		    config=mega-${mc}-r${r}-${center}-${cluster}-feb2016
		
		    echo $config >> ../run22bk11$snap
		
		    dir=/vol/euclid1/euclid1_1/dapple/bk11_lensing/snap$snap/intlength400/$config
		
		    if [ ! -e $dir ]; then
			mkdir $dir
		    fi
		    
		    cat megacam.py bk11.py ${mc}.py scanpdf.py r${r}.py > $dir/config.py


		    echo "targetz=$zcluster" >> $dir/config.py
		    echo "nperarcmin=$ndensity" >> $dir/config.py
		    echo "shapenoise=$shapenoise" >> $dir/config.py
		    echo "beta=$beta" >> $dir/config.py


		    if [ "$center" = "xrayNONE" ]; then
			cat core_none.py >> $dir/config.py

		    elif [ "$center" = "xraymag" ]; then
			cat xraymagneticum.py >> $dir/config.py

		    elif [ "$center" = "szanalytic" ]; then
			cat szanalytic.py >> $dir/config.py
			cat core_${coresizeindex}.py >> $dir/config.py
			echo "szbeam=1.2" >> $dir/config.py
			echo "sz_xi=$spt_xi" >> $dir/config.py

		    elif [ "$center" = "szmag" ]; then
			cat szmagneticum.py >> $dir/config.py
			cat core_${coresizeindex}.py >> $dir/config.py

		    fi


		done
   		
	    done
	    	
	done
    
    }

done
	
