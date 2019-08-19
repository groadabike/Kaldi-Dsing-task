# setup_env.sh

# Sharc HPC
if [[ "$HOSTNAME" == *"sharc"* ]]; then
   # Set Python2.7
    module load apps/python/conda

    # CUDA + GCC
    module load libs/CUDA/9.0.176/binary
    module load libs/cudnn/7.3.1.20/binary-cuda-9.0.176
    module load dev/gcc/5.4

    # Add SOX PATH
    export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/home/acp13gr/apps/sox/lib
    export PATH=$PATH:/home/acp13gr/apps/sox/bin
fi

source activate py27