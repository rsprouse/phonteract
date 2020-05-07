from bokeh.models import ColumnDataSource, Div
from bokeh.plotting import figure
from bokeh.models import BoxSelectTool, BoxZoomTool, PanTool, \
  RedoTool, ResetTool, TapTool, UndoTool, WheelPanTool, \
  WheelZoomTool, ZoomInTool, ZoomOutTool, \
  Button, CustomJS, Div, Markup, Model, TextInput
from bokeh.util.compiler import JavaScript
import numpy as np

class WaveformPlot():
    '''A waveform plot.'''
    def __init__(self, wav, fs, offset=0.0, dtype=np.float32, title='Waveform'):
        self.dtype = dtype
        self.wav = wav.astype(dtype)
        self.fs = fs
        self.offset = dtype(offset)
        self.title = title
        self.source = ColumnDataSource(
            data={
                'time':((np.arange(len(wav)) / fs) + self.offset).astype(dtype),
                'amplitude': self.wav
            }
        )
        self.playbutton = Button(label='Play window')
        self.zoomrange = np.array([0, len(self.wav) / self.fs])
        self.boxzoomtool = BoxZoomTool(dimensions='width')
        self.plot = figure(title=self.title, tools=[self.boxzoomtool, 'reset'])
        self.plot.toolbar.logo = None
        self.plot.line('time', 'amplitude', source=self.source)
        self.winstart_ti = TextInput(
            name="winstart_ti", visible=False, value=str(self.zoomrange[0])
        )
        self.winend_ti = TextInput(
            name="winend_ti", visible=False, value=str(self.zoomrange[1])
        )
        self.fs_ti = TextInput(name="fs_ti", visible=False, value=str(self.fs))
        self.plot.x_range.on_change('start', self.range_cb)
        self.plot.x_range.on_change('end', self.range_cb)

        self.js_playwin_cb = CustomJS(args=dict(sig=self.wav), code='''
            let winstart_ti = document.getElementsByName("winstart_ti")[0];
            let winend_ti = document.getElementsByName("winend_ti")[0];
            let fs_ti = document.getElementsByName("fs_ti")[0];
            if (typeof(winstart_ti) !== 'undefined' &&
                typeof(winend_ti) !== 'undefined' &&
                typeof(fs_ti) !== 'undefined'
            ) {
                let fs = Number(fs_ti.value);
                let start_idx = Math.round(Number(winstart_ti.value) * fs);
                let end_idx = Math.round(Number(winend_ti.value) * fs);
                if (start_idx < 0) {
                    start_idx = 0;
                }
                if (end_idx > sig.length) {
                    end_idx = sig.length;
                }
                let mysig = sig.slice(start_idx, end_idx);

                //
                // For more on AudioBuffer usage see
                // https://developer.mozilla.org/en-US/docs/Web/API/AudioBuffer
                //
                let audioCtx = new (window.AudioContext || window.webkitAudioContext)();

                // Create an empty mono buffer at the signal sample rate.
                let myArrayBuffer = audioCtx.createBuffer(1, mysig.length, fs);

                // Fill the buffer with mysig.
                // This would be cleaner if mysig were of type Float32Array
                // so we could use copyToChannel().
                //myArrayBuffer.copyToChannel(mysig, 0);
                for (var chan = 0; chan < myArrayBuffer.numberOfChannels; chan++) {
                    // This gives us the actual array that contains the data
                    let nowBuffering = myArrayBuffer.getChannelData(chan);
                    for (let i = 0; i < myArrayBuffer.length; i++) {
                        nowBuffering[i] = mysig[i];
                    }
                }

                // Get an AudioBufferSourceNode.
                // This is the AudioNode to use when we want to play an
                // AudioBuffer
                let source = audioCtx.createBufferSource();
                source.buffer = myArrayBuffer;
                source.connect(audioCtx.destination);
                // Start the source playing.
                source.start();
            }
        ''')
        self.playbutton.js_on_click(self.js_playwin_cb)
        self.js_winrange_cb = CustomJS(code="""
//            cbo = cb_obj;
            console.log(cb_obj);
            let winstart_ti = document.getElementsByName("winstart_ti")[0];
            if (typeof(winstart_ti) !== 'undefined') {
                winstart_ti.value = String(cb_obj["start"]);
                console.log(winstart_ti.value);
            }
            let winend_ti = document.getElementsByName("winend_ti")[0];
            if (typeof(winend_ti) !== 'undefined') {
                winend_ti.value = String(cb_obj["end"]);
                console.log(winend_ti.value);
            }
    """
        )
        self.plot.x_range.js_on_change('start', self.js_winrange_cb)
        self.plot.x_range.js_on_change('end', self.js_winrange_cb)

    @property
    def wav_window(self):
        '''Return the data in the currently displayed plot window.'''
        winrange = np.round(self.zoomrange * self.fs).astype(int)
        if winrange[0] < 0:
            winrange[0] = 0
        if winrange[1] > len(self.wav) - 1:
            winrange[1] = len(self.wav) -1
        return self.wav[winrange[0]:winrange[1]]

    @property
    def zoomrange_idx(self):
        '''Return the sample indexes of current zoomrange.'''
        idxs = np.round(self.zoomrange * self.fs).astype(int)
        if idxs[0] < 0:
            idxs[0] = 0
        if idxs[1] > len(self.wav):
            idxs[1] = len(self.wav)
        return idxs

    def range_cb(self, attr, old, new):
        if old is not None:
            if attr == 'start':
                self.zoomrange[0] = new
            elif attr == 'end':
                self.zoomrange[1] = new
#        print(self.zoomrange, self.zoomrange_idx)
