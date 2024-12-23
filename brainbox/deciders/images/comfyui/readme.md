## Symbolic links

BrainBox implementation of ComfyUI doesn't contain a Node Manager, 
because this extension constantly goes online, tries to update things and slows down running the container. 
Hence, it's not very practical to use the BrainBox implementation for experiments and research. 
It's better to have a normal ComfyUI installed.

To share the models between the normal ComfyUI and the BrainBox implementation,
it is convenient to use symbolic links:

`ln -s /path/to/folder2 /path/to/folder1`