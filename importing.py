def mat(directory, session=None):
    from scipy.io import loadmat
    from numpy import empty
    from os import listdir
    
    directory_files = listdir(directory)
    if 'ECoG_and_Event.mat' in directory_files:
        mat = loadmat(directory+'ECoG_and_Event.mat')
        monkey_data = mat['ECoG'].astype(float)
        return monkey_data

    elif 'ECoG_ch1.mat' in directory_files:
        n_channels =len([s for s in directory_files if 'ECoG_ch' in s])

        file_base = directory+'ECoG_ch'
        variable_base = 'ECoGData_ch'

        f = str.format('{0}{1}.mat', file_base, 1)
        v = str.format('{0}{1}', variable_base, 1)
        n_datapoints = loadmat(f)[v].shape[1]

        monkey_data = empty((n_channels,n_datapoints))

        for i in range(n_channels):
            f = str.format('{0}{1}.mat', file_base, i+1)
            v = str.format('{0}{1}', variable_base, i+1)
            monkey_data[i,:] = loadmat(f)[v]
        return monkey_data
    elif session and 'CSC1-%i.mat'%session in directory_files:
        n_channels =len([s for s in directory_files if 'CSC' in s and '-%i.mat'%session in s])

        file_base = directory+'CSC'
        v = 'X'

        f = str.format('{0}{1}-{2}.mat', file_base, 1, session)
        n_datapoints = loadmat(f)[v].shape[1]

        monkey_data = empty((n_channels,n_datapoints))

        for i in range(n_channels):
            f = str.format('{0}{1}-{2}.mat', file_base, i+1, session)
            monkey_data[i,:] = loadmat(f)[v]
        return monkey_data
    else:
        print("Unsupported data format")
        return
