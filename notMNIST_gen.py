# -*- coding: utf-8 -*-
"""
Created on Mon Dec 26 09:53:22 2016

@author: RMFit
"""
def make_composite_dataset():
    # Imports
    import os
    import cv2
    import sys
    import random
    import tarfile
    import numpy as np
    from six.moves.urllib.request import urlretrieve
    from matplotlib.patches import Rectangle
    
    url = 'http://commondatastorage.googleapis.com/books1000/'
    num_classes = 10
    image_size = 28  # Pixel height.
    np.random.seed(1)
            
    def maybe_download(filename, expected_bytes, force=False):
      """Download a file if not present, and make sure it's the right size."""
      if force or not os.path.exists(filename):
        print('Attempting to download:', filename) 
        filename, _ = urlretrieve(url + filename, filename)
        print('\nDownload Complete!')
      statinfo = os.stat(filename)
      if statinfo.st_size == expected_bytes:
        pass
      else:
        raise Exception(
          'Failed to verify ' + filename + '. Can you get to it with a browser?')
      return filename
    
    def maybe_extract(filename, force=False):
      root = os.path.splitext(os.path.splitext(filename)[0])[0]  # remove .tar.gz
      if os.path.isdir(root) and not force:
        # You may override by setting force=True.
        pass
      else:
        print('Extracting data for %s. This may take a while. Please wait.' % root)
        tar = tarfile.open(filename)
        sys.stdout.flush()
        tar.extractall()
        tar.close()
      data_folders = [
        os.path.join(root, d) for d in sorted(os.listdir(root))
        if os.path.isdir(os.path.join(root, d)) and (len(d) == 1)]
      if len(data_folders) != num_classes:
        raise Exception(
          'Expected %d folders, one per class. Found %d instead.' % (
            num_classes, len(data_folders)))
      return data_folders
    
    def load_letter(folder, min_num_images):
      """Load the data for a single letter label."""
      image_files = os.listdir(folder)
      dataset = np.ndarray(shape=(len(image_files), image_size, image_size),
                             dtype=np.uint8)
      num_images = 0
      for image in image_files:
        image_file = os.path.join(folder, image)
        try:
          image_data = cv2.imread(image_file, 0)
          if isinstance(image_data, np.ndarray):
              if (image_data.shape != (image_size, image_size)):
                  raise Exception('Unexpected image shape: %s' % str(image_data.shape))
              dataset[num_images, :, :] = image_data
              num_images = num_images + 1
        except IOError as e:
          print('Could not read:', image_file, ':', e, '- it\'s ok, skipping.')
        
      dataset = dataset[0:num_images, :, :]
      if num_images < min_num_images:
        raise Exception('Many fewer images than expected: %d < %d' %
                        (num_images, min_num_images))
        
      print('Full dataset tensor:', dataset.shape)
      print('Mean:', np.mean(dataset))
      print('Standard deviation:', np.std(dataset))
      return dataset
    
    def maybe_savez(data_folders, min_num_images_per_class, force=False):
      dataset_name = data_folders[0][:-1]+'images.npz'
      dataset = {}
      if force or not os.path.exists(dataset_name):
          for folder in data_folders:
              print folder[-1],
              dataset[folder[-1:]]= load_letter(folder, min_num_images_per_class)
          try:
            np.savez(dataset_name, **dataset)
          except Exception as e:
            print('Unable to save data to', dataset_name, ':', e)
      return dataset_name
      
    def gen_data_dict(dataset):
      data_dict = {}
      all_data = np.load(dataset)
      for letter in all_data.files: 
        try:
          data_dict[letter] = all_data[letter]
        except Exception as e:
          print('Unable to process data from', dataset, ':', e)
          raise
      all_data.close()
      return data_dict
    
    def gen_dataset(source_dict, data_samples=10000, min_digits=3, max_digits=5, 
                    image_width=28, image_height=28, image_buffer=4, frame_buffer=4):
        
        frame_width = frame_buffer*2 + (image_width + image_buffer * 2) * max_digits
        frame_height = frame_buffer*2 + (image_height + image_buffer * 2)
        dataset = np.zeros((data_samples, frame_height, frame_width), np.uint8)
        #dataset = np.random.randint(0, 256, (data_samples, frame_height, frame_width), 
        #                            np.uint8)
        labels = np.ndarray((data_samples), dtype=np.dtype('a'+str(max_digits)))
        for i in range(data_samples):
            sample_len = random.randint(min_digits, max_digits)
            label = ''
            for j in range(max_digits):
                if j <= sample_len:
                    letter = random.choice(source_dict.keys())
                    image = np.array(random.choice(source_dict[letter]))
                else:
                    letter = '_'
                    image = np.zeros((image_height, image_width), np.uint8)
#                    image = np.random.randint(0, 256, (image_height, image_width), 
#                                              np.uint8)
                v_offset = frame_buffer + image_buffer
                h_offset = frame_buffer + j * (image_width + image_buffer * 2)
                dataset[i, v_offset : v_offset + image_width, 
                        h_offset : h_offset + image_height] = image
                label += letter
            labels[i] = label
        return dataset, labels

    def get_position(image_size, last_pos, constraint):
        valid = False
#        print(last_pos, constraint)
        while not valid:
            x = np.random.randint(last_pos[0], constraint)
            y = np.random.randint(last_pos[1], constraint)
            if x > (last_pos[0] + image_size) and (y > 0):
                valid = True
            if y > (last_pos[1] + image_size) and (x > 0):
                valid = True
        return (x, y)
        
    def gen_dataset_2(source_dict, data_samples=10000, min_digits=1, max_digits=5, 
                    image_size=28, frame_size=128, image_buffer=2):
        dataset = np.zeros((data_samples, frame_size, frame_size), np.uint8)
        bound_box = np.zeros((data_samples, max_digits, 2, 2), np.uint8)
        labels = np.ndarray((data_samples), dtype=np.dtype('a'+str(max_digits)))
        for i in range(data_samples):
            working_digits = random.randint(min_digits, max_digits)
            sample_len = random.randint(min_digits, working_digits)
#            canvas_size = image_buffer*2 + (image_size + image_buffer*2) * working_digits
            canvas_size = image_buffer*2 + (image_size + image_buffer*2) * sample_len
            canvas = np.zeros((canvas_size, canvas_size), np.uint8)
            label = ''
            position = (image_buffer-image_size, image_buffer-image_size)
            ratio = float(frame_size) / float(canvas_size)
            for j in range(sample_len):
                letter = random.choice(source_dict.keys())
                image = np.array(random.choice(source_dict[letter]))
                constraint = canvas_size - (image_buffer + (image_size + image_buffer) * (sample_len - j))
                position = get_position(image_size, position, constraint)
                place = position[0], position[0]+image_size, position[1], position[1]+image_size
                canvas[place[0]:place[1], place[2]:place[3]] = np.copy(image)
                bound_box[i, j, 0, :] = int(round(place[0] * ratio)), int(round(place[2] * ratio))
                bound_box[i, j, 1, :] = int(round(place[1] * ratio)), int(round(place[3] * ratio))
                label += letter
            label += ' '*(max_digits-len(label))
            dataset[i, 0:frame_size, 0:frame_size] = cv2.resize(np.copy(canvas), (frame_size, frame_size))
            labels[i] = label
        return dataset, bound_box, labels

        
      
    print('Starting')
    train_filename = maybe_download('notMNIST_large.tar.gz', 247336696)
    test_filename = maybe_download('notMNIST_small.tar.gz', 8458043)
    print('Download Complete')
    
    
    train_folders = maybe_extract(train_filename)
    test_folders = maybe_extract(test_filename)
    print('Extract Complete')

    train_datasets = maybe_savez(train_folders, 45000)
    test_datasets = maybe_savez(test_folders, 1800)
    print('Saving Complete')
    
    
    train_image_data = gen_data_dict(train_datasets)
    test_image_data = gen_data_dict(test_datasets)
    print('Data Dictionaries Built')
    
    def gen_composite(train_data = train_image_data, test_data = test_image_data, force = False):
        dataset_name = 'notMNIST_ML_data.npz'
        force = True
        if force or not os.path.exists(dataset_name):
            train_dataset, train_box, train_labels = gen_dataset_2(train_data, 200000)
            valid_dataset, valid_box, valid_labels = gen_dataset_2(train_data)
            test_dataset, test_box, test_labels = gen_dataset_2(test_data)
            dataset = {'train_dataset':train_dataset, 'train_labels':train_labels,
                       'valid_dataset':valid_dataset, 'valid_labels':valid_labels,
                       'test_dataset':test_dataset, 'test_labels':test_labels}
            try:
                np.savez(dataset_name, **dataset)
            except Exception as e:
                print('Unable to save data to', dataset_name, ':', e)
        else:
            try: 
                dataset = np.load(dataset_name)
                train_dataset = dataset['train_dataset']
                train_labels = dataset['train_labels']
                valid_dataset = dataset['valid_dataset']
                valid_labels = dataset['valid_labels']
                test_dataset = dataset['test_dataset']
                test_labels = dataset['test_labels']
                dataset.close()
            except Exception as e:
              print('Unable to process data from', dataset, ':', e)
              raise
        print(dataset_name)
        return train_dataset, train_labels, valid_dataset, valid_labels, test_dataset, test_labels
    
    
    train_dataset, train_labels, valid_dataset, valid_labels, test_dataset, test_labels = gen_composite()
    
    dataset = {}
    dataset['train_dataset'] = train_dataset
    dataset['train_labels'] = train_labels
    dataset['valid_dataset'] = valid_dataset
    dataset['valid_labels'] = valid_labels
    dataset['test_dataset'] = test_dataset
    dataset['test_labels'] = test_labels
    
    import matplotlib.pyplot as plt
    plt.imshow(train_dataset[0])
#    plt.show()
    print(train_labels[0])
#    return gen_dataset(test_image_data)
    return dataset

mnist_data = make_composite_dataset()
import matplotlib.pyplot as plt
plt.imshow(mnist_data['train_dataset'][0])
