#!/bin/bash -u

binning=linearbins12

rm ../run14a.*

for snap in 124 141; do

    cat megacam_siminput.list | { 

	while read cluster zcluster ndensity beta core coreindex; do 

	    for mc in c4 duffy; do
	    
		for r in 6 9; do
		    
		    for shapenoise in 0.25; do

			for coresize in $coreindex none; do
	    
			    config=mega-${mc}-r${r}-sigma${shapenoise}-core${coresize}-${cluster}
			    dir=../../bk11_lensing/snap$snap/intlength400/$config
			    mkdir $dir
			    cat scanpdf.sh bk11.sh ${mc}.sh r${r}.sh core_${coresize}.sh ${binning}.sh > $dir/config.sh
			    echo "targetz=$zcluster" >> $dir/config.sh
			    echo "nperarcmin=$ndensity" >> $dir/config.sh
			    echo "shapenoise=$shapenoise" >> $dir/config.sh
			    echo "beta=$beta" >> $dir/config.sh
			    
			    
			    echo $config >> ../run14a.${snap}
		    
			done
			
		    done
   		    
		done
		
	    done
	    
	done
    
    }

done


	
