from avalanchetoolbox import avalanches
from avalanchetoolbox import database as db
import h5py
import os

from Helix_database import Session, database_url
session = Session()
swarms_directory = '/home/alstottj/biowulf/swarms/'
python_location= '/usr/local/Python/2.7.2/bin/python'

analyses = avalanches.Analyses(database_url, verbose=True)
analyses.time_scales = [1, 2, 3, 4, 5, 6, 7, 8, 16, 32]
analyses.threshold_mode = 'Likelihood'
analyses.threshold_levels = [2, 5, 10]
analyses.threshold_directions = ['both']
#given_xmin_xmax = [(None, None), (1, None), (1, 'channels')]
analyses.vent_signals = ['displacement']
analyses.event_detections = ['local_extrema']#, 'local', 'excursion_extrema']
analyses.cascade_methods = ['grid']
analyses.spatial_samples = [('all', 'all')]
analyses.temporal_samples = [('all', 'all')]


sampling_rate = 1000.0

data_path = '/data/alstottj/RIKEN/For_Analysis/'
filter_type = 'FIR'
taps = 25
window = 'hamming'
ds_rate = 1000.0
transd = True
mains = 50

visits = ['', '0', '1','2','3','4','5','6','7','8']
tasks = ['food_tracking', \
        'visual_grating',\
        'visual_grating',
        'emotional_movie', \
        'social_competition',\
        'rest', 'anesthetized', 'sleep_wake_transition']

rem=False
rest='rested'
drug='none'

dirList=os.listdir(data_path)
for fname in dirList:
    file = data_path+fname
    f = h5py.File(file)
    group_name = f.attrs['group_name'] 
    number_in_group = f.attrs['number_in_group']
    species = f.attrs['species']
    location = f.attrs['location']

    subject = session.query(db.Subject).\
            filter_by(species=species, group_name=group_name, name=number_in_group).first()
    if not subject:
        subject = db.Subject(species=species, group_name=group_name, name=number_in_group)
        session.add(subject)
        session.commit()

    print file

    conditions = [(t,v) for t in tasks for v in visits] 
    for task_type, visit in conditions:
        base = task_type+visit
        base_filtered = base+'/filter_'+filter_type+'_'+str(taps)+'_'+window+'_ds-'+str(ds_rate)
        print base_filtered 
        #If this particular set of conditions doesn't exist for this subject, just continue to the next set of conditions
        try:
            f[base_filtered]
        except KeyError:
            continue
        print base

        duration = f[base+'/raw/displacement'].shape[1]

        task = session.query(db.Task).\
                filter_by(type=task_type).first()
        if not task:
            print('Task not found! Adding.')
            task = db.Task(type=task_type)
            session.add(task)
            session.commit()

        sensor = session.query(db.Sensor).\
                filter_by(location=number_in_group, sensor_type='ECoG').first()
        if not sensor:
            print('Sensor not found! Adding.')
            sensor = db.Sensor(location=number_in_group, sensor_type='ECoG')
            session.add(sensor)
            session.commit()
        
        if visit=='':
            visit_number=None
        else:
            visit_number=int(visit)
        experiment = session.query(db.Experiment).\
                filter_by(location=location, subject_id=subject.id, visit_number=visit_number, mains=mains, drug=drug,\
                rest=rest, task_id=task.id).first()
        if not experiment:
            experiment = db.Experiment(location=location, subject_id=subject.id, visit_number=visit_number, mains=mains, drug=drug,\
                rest=rest, task_id=task.id)
            session.add(experiment)
            session.commit()


        recording = session.query(db.Recording).\
                filter_by(experiment_id=experiment.id, sensor_id=sensor.id, duration=duration, \
                subject_id = subject.id, task_id=task.id,\
                sampling_rate=sampling_rate, eye_movement_removed=rem, transd=transd).first()
        if not recording:
            recording = db.Recording(experiment_id=experiment.id, sensor_id=sensor.id, duration=duration,\
                    subject_id = subject.id, task_id=task.id,\
                    sampling_rate=sampling_rate, eye_movement_removed=rem, transd=transd)
            session.add(recording)
            session.commit()

        for band in list(f[base_filtered]):
            print band
            data = f[base_filtered+'/'+band]
            band_range = data.attrs['frequency_range']
            downsampled_rate = data.attrs['downsampled_rate']
            if band_range.shape[0]==1:
                band_min=0.
                band_max=band_range[0]
            else:
                band_min=band_range[0]
                band_max=band_range[1]

            filter = session.query(db.Filter).\
                    filter_by(recording_id=recording.id, filter_type=filter_type, poles=taps-1, window=window,\
                    band_name=band, band_min=band_min, band_max=band_max, duration=data['displacement'].shape[1],\
                    downsampled_rate=downsampled_rate, notch=False,phase_shuffled=False).first()
            if not filter:
                filter = db.Filter(\
                    recording_id=recording.id, filter_type=filter_type, poles=taps-1, window=window,\
                    band_name=band, band_min=band_min, band_max=band_max, duration=data['displacement'].shape[1],\
                    downsampled_rate=downsampled_rate, notch=False,phase_shuffled=False,\
                    subject_id = subject.id, task_id=task.id, experiment_id=experiment.id, sensor_id=sensor.id)

                session.add(filter)
                session.commit()

            analyses.filename = f.file.filename
            analyses.HDF5_group = base_filtered+'/'+band
            analyses.submit(filter.id, memory_requirement=8)
session.close()
session.bind.dispose()
