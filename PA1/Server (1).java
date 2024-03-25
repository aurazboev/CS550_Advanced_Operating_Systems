import java.io.*;
import java.net.ServerSocket;
import java.net.Socket;
import java.util.Collections;
import java.util.HashSet;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;

public class Server {

    private static final ConcurrentHashMap<String, Set<String>> index = new ConcurrentHashMap<>();

    public static void main(String[] args) {
	Server server = new Server();
	server.Start();
    }
    public void Start(){
            int port = 9876;
        try{
            	ServerSocket serverSocket = new ServerSocket(port);
		System.out.println("Server is listening on port " + port);
		waitForConnections(serverSocket); 
	   }
	catch (IOException ex) {
		System.out.println("Server exception: " + ex.getMessage());
		ex.printStackTrace();
        }
    }
    private void waitForConnections(ServerSocket serverSocket){
	try{
		while (true) {
			Socket socket = serverSocket.accept();
            System.out.println("New client connected with ip address: " + socket.getInetAddress().getHostAddress());
			Thread serverThread = new Thread(new ServerThread(socket));
		serverThread.start();
            		}
	    } 
	catch (IOException ex) {
            System.out.println("Server exception: " + ex.getMessage());
            ex.printStackTrace();
        }
   }
    private class ServerThread implements Runnable {
        private final Socket socket;

        public ServerThread(Socket socket) {
            this.socket = socket;
        }

        @Override
        public void run() {
            try {
		BufferedReader reader = new BufferedReader(new InputStreamReader(socket.getInputStream()));
		PrintWriter writer = new PrintWriter(new OutputStreamWriter(socket.getOutputStream()), true);
                String clientIP = socket.getInetAddress().getHostAddress();
                String command;
                while ((command = reader.readLine()) != null) {
                    if (command.startsWith("register")) {
                        String fileName = reader.readLine();
                        register(fileName, clientIP);
                        writer.println("Registered: " + fileName + " from " + clientIP);
                    } else if (command.startsWith("search")) {
                        String fileName = command.split(" ")[1];
                        Set<String> ips = search(fileName);
                        writer.println("IPs containing " + fileName + ": " + ips);
                    } else {
                        writer.println("Invalid command: " + command);
                    }
                }
            } catch (IOException ex) {
                System.out.println("ClientHandler exception: " + ex.getMessage());
            }
        }

        private void register(String fileName, String clientIP) {
        if(!index.containsKey(fileName)){
        	Set<String> clientIPSet = Collections.synchronizedSet(new HashSet<>());
        	index.put(fileName,clientIPSet);
        	}
       	index.get(fileName).add(clientIP);
        }

        private Set<String> search(String fileName) {
            return index.getOrDefault(fileName, Collections.emptySet());
        }
    }
}
