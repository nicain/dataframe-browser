import os
import matplotlib.pyplot as plt
import numpy as np
import itertools

from allensdk.core.brain_observatory_nwb_data_set import BrainObservatoryNwbDataSet
import allensdk.brain_observatory.roi_masks as roi_masks

from dataframe_browser.mappers import png

@png
def nwb_file_to_max_projection(nwb_file):
    data_set = BrainObservatoryNwbDataSet(nwb_file)
    max_projection_img = data_set.get_max_projection()

    # roi_mask_array = roi_masks.create_roi_mask_array(data_set.get_roi_mask())
    # border_set = set()
    # for roi_mask_img in roi_mask_array:
    #     for ii, jj in zip(*np.where(roi_mask_img==1)):
    #         for di, dj in itertools.product([-1,0,1], [-1,0,1]):
    #             if roi_mask_img[ii+di, jj+dj] == 0:
    #                 border_set.add((ii+di, jj+dj))

    # border_ii, border_jj = zip(*list(border_set))

    # border_mask = np.zeros((roi_mask_array.shape[1], roi_mask_array.shape[2], 4)).astype(max_projection_img.dtype)
    # border_mask[border_ii, border_jj,0] = np.iinfo(max_projection_img.dtype).max
    # border_mask[border_ii, border_jj,3] = np.iinfo(max_projection_img.dtype).max

    fig, ax = plt.subplots(1,1)
    ax.imshow(max_projection_img, cmap=plt.cm.gray, clim=(max_projection_img.min(), np.percentile(max_projection_img.flatten(), 98)))
    # ax.imshow(border_mask)
    ax.set_xticks([])
    ax.set_yticks([])

    return fig

@png
def plot_traces_heatmap(nwb_file):

    data_set = BrainObservatoryNwbDataSet(nwb_file)

    _, dff_traces = data_set.get_dff_traces()

    fig, ax = plt.subplots(figsize=(20, 8))
    cax = ax.pcolormesh(dff_traces, cmap='magma', vmin=0, vmax=np.percentile(dff_traces, 99))
    ax.set_ylim(0, dff_traces.shape[0])
    ax.set_xlim(0, dff_traces.shape[1])
    ax.set_ylabel('cells')
    ax.set_xlabel('2P frames')
    cb = plt.colorbar(cax, pad=0.015)
    cb.set_label('dF/F', labelpad=3)

    return fig


    



