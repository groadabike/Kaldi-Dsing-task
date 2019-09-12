# setup_env.sh

# Sharc HPC
if [[ "$HOSTNAME" == *"sharc"* ]]; then
    module load apps/python/conda
    module load libs/CUDA/9.0.176/binary
    module load libs/cudnn/7.3.1.20/binary-cuda-9.0.176
    module load dev/gcc/5.4
    module load libs/icu/58.2/gcc-4.9.4
    PATH=$PATH:/usr/local/packages/libs/icu/58.2/gcc-4.9.4/bin
    module load libs/intel-mkl/2019.3/binary

    # Add SOX PATH
    LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/home/acp13gr/apps/sox/lib
    PATH=$PATH:/home/acp13gr/apps/sox/bin
    source activate py35
fi

