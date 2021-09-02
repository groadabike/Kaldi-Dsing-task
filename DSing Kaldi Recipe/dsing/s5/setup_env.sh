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
    source activate py27
fi
if [[ "$HOSTNAME" == *"bessemer"* ]]; then
    module load Anaconda3/5.3.0
    source activate py27
    module load fosscuda/2019a
    module load imkl/2019.1.144-iimpi-2019a

    # Sox PATH
    LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$HOME/apps/sox/lib
    PATH=$PATH:$HOME/apps/sox/bin
fi

