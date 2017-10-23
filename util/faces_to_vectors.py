import os
import ntpath
import argparse
from sys import exit
from matplotlib import pyplot as plt

import json

import tensorflow as tf
import facenet


def get_image_paths(inpath):
    paths = []

    for file in os.listdir(inpath):
        if os.path.isfile(os.path.join(inpath, file)):
            if file.lower().endswith(('.png', '.jpg', '.jpeg')) is False:
                continue

            paths.append(os.path.join(inpath, file))

    return (paths)


def faces_to_vectors(inpath, modelpath, outpath, imgsize, batchsize=100):
    '''
    Given a folder and a model, loads images and performs forward pass to get a vector for each face
    results go to a JSON, with filenames mapped to their facevectors
    :param inpath: Where are your images? Must be cropped to faces (use MTCNN!)
    :param modelpath: Where is the tensorflow model we'll use to create the embedding?
    :param outpath: Full path to output file (better give it a JSON extension)
    :return: Number of faces converted to vectors
    '''
    results = dict()

    with tf.Graph().as_default():
        with tf.Session() as sess:

            facenet.load_model(modelpath)
            mdl = None

            image_paths = get_image_paths(inpath)

            # Get input and output tensors
            images_placeholder = tf.get_default_graph().get_tensor_by_name("input:0")
            embeddings = tf.get_default_graph().get_tensor_by_name("embeddings:0")
            phase_train_placeholder = tf.get_default_graph().get_tensor_by_name("phase_train:0")

            # Let's do them in batches, don't want to run out of memory
            for i in range(0, len(image_paths), batchsize):
                images = facenet.load_data(image_paths=image_paths[i:i+batchsize], do_random_crop=False, do_random_flip=False, image_size=imgsize, do_prewhiten=True)
                feed_dict = {images_placeholder: images, phase_train_placeholder: False}

                emb_array = sess.run(embeddings, feed_dict=feed_dict)
                for j in range(0, len(emb_array)):
                    results[ntpath.basename(image_paths[i+j])] = emb_array[j].tolist()

    # All done, save for later!
    json.dump(results, open(outpath, "w"))

    return len(results.keys())

def vectors_to_plots(vectorpath, pltpath):
    if os.path.isdir(pltpath) is not True:
        return False

    vector_file = open(vectorpath).read()
    num_plotted = 0
    vector_data = json.loads(vector_file)
    for image_name in vector_data.iterkeys():
        plt.plot(vector_data[image_name])
        plt.savefig(pltpath + image_name)
        plt.close()
        num_plotted += 1

    return num_plotted

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--inpath", help="Folder with images - png/jpg/jpeg - of faces", type=str, required=True)
    parser.add_argument("--outpath", help="Full path to where you want the results JSON", type=str, required=True)
    parser.add_argument("--mdlpath", help="Where to find the Tensorflow model to use for the embedding", type=str, required=True)
    parser.add_argument("--imgsize", help="Size of images to use", type=int, default=160, required=False)
    parser.add_argument("--pltpath", help="Full path to dir where you want the vector visualisations", type=str, required=False)
    args = parser.parse_args()

    num_images_processed = faces_to_vectors(args.inpath, args.mdlpath, args.outpath, args.imgsize)
    if num_images_processed > 0:
        print("Converted " + str(num_images_processed) + " images to face vectors.")
    else:
        print("No images were processed - are you sure that was the right path? [" + args.inpath + "]")
        return False

    if args.pltpath is not "":
        num_images_plotted = vectors_to_plots(args.outpath, args.pltpath)
        if num_images_plotted > 0:
            print("Plotted " + str(num_images_plotted) + " face vectors to dir [" + args.pltpath + "]")
        else:
            print("No vectors were plotted - are you sure you provided a valid output path? [" + args.pltpath + "]")
        return False

    return True


if __name__ == main():
    if main() is False:
        exit(-1)

    exit(0)
