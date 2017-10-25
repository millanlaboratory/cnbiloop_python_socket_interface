using System.Collections;
using System.Collections.Generic;
using System.Threading;
using System;
using UnityEngine;
using System.Text;

using System.Net;
using System.Net.Sockets;


public class cnbiloop : MonoBehaviour {


    //UDP for MATLAB, by PK
    bool MATLABCommand = true;
    private string remoteIPPythonLoop = "127.0.0.1";
    //private string remoteIPPythonLoop = "192.168.1.1";
    private int localPortGetTOBIID = 9999; 
    private int localPortSendTOBIID = 9990;
    private IPEndPoint remoteEndPointGetTOBIID;
    private IPEndPoint remoteEndPointSendTOBIID;
    private UdpClient clientGetTOBIID;
    private UdpClient clientSendTOBIID;

    private Socket sockListenTID;
    private Socket sockSendTID;
    private Socket sock2 = null;
    private byte [] _receiveBuffer = new byte [1024];
    private byte [] receiveBuffer = new byte [1024];
    private int TIDEvent = -1;
    private int bufferStart = 0;
    private int buffRemain = 0;
    private byte [] bufConvert = new byte [10];
    
    private byte [] bytes = new byte [1024];

    private bool firstCall = true;

    [HideInInspector]
    public int [] evtCntr; // event counter
    [HideInInspector]
    public int[] evtCntrClean; // event counter
    [HideInInspector]
    public bool eventUsed = false;
    public bool newEvent = false;
    public int updateRate = 16; // Hz for cl_runloop or cl_runloopscope

    public bool getTID = true;
    public bool sendTID = true;
    public bool sendDone = true;
    private bool getTIDServerSet = false;
    private bool sendTIDServerSet = false;

    private TrajectoryManagement trajMang;

    // Use this for initialization
    void Start () {
        trajMang = GameObject.Find("Trajectory").gameObject.GetComponent<TrajectoryManagement>();
        getTIDServerSet = !getTID;
        sendTIDServerSet = !sendTID;
        while (!getTIDServerSet || !sendTIDServerSet)
        {
            try
            {
                if(getTID && !getTIDServerSet)
                {
                    // Establish connection to the python interface FOR RECEIVING
                    sockListenTID = new Socket(AddressFamily.InterNetwork, SocketType.Stream, ProtocolType.Tcp);
                    remoteEndPointGetTOBIID = new IPEndPoint(IPAddress.Parse(remoteIPPythonLoop), localPortGetTOBIID);
                    sockListenTID.Connect(remoteEndPointGetTOBIID);
                    getTIDServerSet = true;
                }

                if(sendTID && !sendTIDServerSet)
                {
                    // Establish connection to the python interface FOR SENDING
                    sockSendTID = new Socket(AddressFamily.InterNetwork, SocketType.Stream, ProtocolType.Tcp);
                    remoteEndPointSendTOBIID = new IPEndPoint(IPAddress.Parse(remoteIPPythonLoop), localPortSendTOBIID);
                    sockSendTID.Connect(remoteEndPointSendTOBIID);
                    sendTIDServerSet = true;
                }
            }
            catch (Exception err)
            {
                print(err.ToString());
                Debug.Assert(false);
            }
        }
        evtCntr = new int [3];
        for(int i = 0; i < evtCntr.Length; i++)
            evtCntr[i] = 0;
        evtCntrClean = new int[3];
        for (int i = 0; i < evtCntrClean.Length; i++)
            evtCntrClean[i] = 0;
    }

    public void SendTIDEvent(int eventCode)
    {
        sendDone = false;
        string data = eventCode.ToString() + ',';
        // Convert the string data to byte data using ASCII encoding.  
        byte[] byteData = Encoding.ASCII.GetBytes(data);

        Debug.Log(string.Format("Sennding {0}", byteData));
        // Begin sending the data to the remote device.  
        sockSendTID.BeginSend(byteData, 0, byteData.Length, 0,
            new AsyncCallback(SendCallback), sockSendTID);
    }

    void SendCallback(IAsyncResult ar)
    {
        try
        {
            // Retrieve the socket from the state object.  
            ///Socket client = (Socket)ar.AsyncState;

            // Complete sending the data to the remote device.  
            // int bytesSent = client.EndSend(ar);
            int bytesSent = sockSendTID.EndSend(ar);
            Debug.Log(string.Format("Sent {0} bytes to server.", bytesSent));

            // Signal that all bytes have been sent.  
            sendDone = true;
        }
        catch (Exception e)
        {
            Console.WriteLine(e.ToString());
        }
    }

    public void startReceiving()
    {
        sockListenTID.BeginReceive(_receiveBuffer, 0, _receiveBuffer.Length, SocketFlags.None, new AsyncCallback(ReceiveCallback), null);
    }

    void ReceiveCallback(IAsyncResult AR)
    {
        Debug.Log("calling");
        //Check how much bytes are received and call EndReceive to finalize handshake
        int received = 0;
        try
        {
           received = sockListenTID.EndReceive(AR);
        }
        catch(Exception err)
        {
            Debug.Log("No data coming from the loop");
            sockListenTID.BeginReceive(_receiveBuffer, 0, _receiveBuffer.Length, SocketFlags.None, new AsyncCallback(ReceiveCallback), null);
            return;
        }


        int cntr = 0;

        //Copy the received data into new buffer, to avoid null bytes
        byte [] recData = new byte [received + buffRemain];
        try
        {

            Buffer.BlockCopy(_receiveBuffer, 0, recData, buffRemain, received);
            if (buffRemain != 0)
                Buffer.BlockCopy(bufConvert, bufferStart, recData, 0, buffRemain);
            //Data Processing, e.g., change the level of assistance or size of waypoints.

            //reset event counter (clean)
            for (int j = 0; j < evtCntrClean.Length; j++)
                evtCntrClean[j] = 0;

            for (int i = 0; i < recData.Length; i++)
            {
                //bufConvert[cntr] = (byte)(recData[i] - 48); // to make '0' as 0
                bufConvert[cntr] = recData[i];
                //Debug.Log("a");
                if (recData[i] != 46) //46 is "."
                {
                    cntr++;
                }
                else
                {
                    byte [] tmp = new byte [cntr];
                    Buffer.BlockCopy(bufConvert, 0, tmp, 0, cntr);                
                    //TIDEvent = Convert.ToInt16(Convert.ToString(tmp[0]));
                    //TIDEvent = BitConverter.ToInt32(tmp, 0);
                    TIDEvent = convertBytesToInt(tmp);
                    newEvent = true;
                    assignEvent(TIDEvent, ref evtCntr);
                    assignNewEvent(TIDEvent, ref evtCntrClean);
                    cntr = 0;
                    if(!firstCall)
                    {
                        Debug.Log("Data received!");
                        Debug.Log(string.Format("Data is {0}", TIDEvent));
                    }
                }
            }
            
        }
        catch (Exception err)
        {
            Debug.Log(err);
        }
        Debug.Log("c");
        buffRemain = cntr;
        bufferStart = recData.Length - cntr;
        if (buffRemain != 0)
            Debug.Log(string.Format("BufferStart is {0}", bufferStart));

        //Start receiving again
        if(!trajMang.startTraj)
        {
            eventUsed = true;
        }
        else if(firstCall)
        {
            //reset event counter
            for (int j = 0; j < evtCntr.Length; j++)
                evtCntr[j] = 0;
            eventUsed = true;
            firstCall = false;
        }
        else
        {
            eventUsed = false;
            newEvent = false;
        }
        sockListenTID.BeginReceive(_receiveBuffer, 0, _receiveBuffer.Length, SocketFlags.None, new AsyncCallback(ReceiveCallback), null);
    }

    private int convertBytesToInt(byte [] ascii)
    {
        int n = ascii.Length;
        int r = 0;
        for (int i = 0; i < n; i++)
        {
            r = r + (int) ((ascii[i] - 48) * Math.Pow(10, n-i-1));
            Debug.Assert((ascii[i] - 47) > 0);
        }
        return r;
    }
    private void assignEvent(int evt, ref int [] evtCntr)
    {
        if (evt >= evtCntr.Length || evt < 0)
        {
            Debug.LogError(string.Format("Event out of index, event: {0}", evt));
            return;
        }
        /*
        if(eventUsed)
        {
            //reset event counter
            for (int i = 0; i < evtCntr.Length; i++)
                evtCntr[i] = 0;
        }*/        
        evtCntr[evt]++;
    }

    private void assignNewEvent(int evt, ref int[] evtCntrClean)
    {
        if (evt >= evtCntrClean.Length || evt < 0)
        {
            Debug.LogError(string.Format("Event out of index, event: {0}", evt));
            return;
        }
        evtCntrClean[evt] = 1;
    }

    void OnApplicationQuit()
    {
        sockListenTID.Close();
        sockListenTID = null;
        //sock2.Close();
        //sock2 = null;
    }

    void Awake()
    {
        
    }

    // Update is called once per frame
    void Update () {
        /*
        sockListenTID.Receive(bytes, bytes.Length, 0);
        
		if(clientGetTOBIID.Available > 0)
            print("123");
            */
	}
}
