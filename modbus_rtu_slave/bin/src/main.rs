use std::future::{self, Future};
use std::net::SocketAddrV4;
use std::pin::Pin;
use std::sync::Arc;
use tokio::sync::Mutex;
use tokio_modbus::client::{tcp, Context};
use tokio_modbus::prelude::*;
use tokio_modbus::server::rtu::Server;

struct Service {
    slave: Slave,
    ctx: Arc<Mutex<Context>>,
}
impl tokio_modbus::server::Service for Service {
    type Request = SlaveRequest<'static>;
    type Response = Option<Response>;
    type Exception = ExceptionCode;
    type Future = Pin<Box<dyn Future<Output = Result<Self::Response, Self::Exception>> + Send>>;

    fn call(&self, req: Self::Request) -> Self::Future {
        let SlaveRequest { slave, request } = req;
        if slave != self.slave.0 {
            return Box::pin(future::ready(Ok(None)));
        }

        match request {
            Request::ReadInputRegisters(addr, cnt) => {
                let ctx = self.ctx.clone();
                let fut = async move {
                    let mut ctx = ctx.lock().await;
                    let rsp = ctx.read_input_registers(addr, cnt).await.unwrap()?;
                    Ok(Some(Response::ReadInputRegisters(rsp)))
                };
                Box::pin(fut)
            }
            Request::ReadHoldingRegisters(addr, cnt) => {
                let ctx = self.ctx.clone();
                let fut = async move {
                    let mut ctx = ctx.lock().await;
                    let rsp = ctx.read_holding_registers(addr, cnt).await.unwrap()?;
                    Ok(Some(Response::ReadHoldingRegisters(rsp)))
                };
                Box::pin(fut)
            }
            Request::ReadCoils(addr, cnt) => {
                let ctx = self.ctx.clone();
                let fut = async move {
                    let mut ctx = ctx.lock().await;
                    let rsp = ctx.read_coils(addr, cnt).await.unwrap()?;
                    Ok(Some(Response::ReadCoils(rsp)))
                };
                Box::pin(fut)
            }
            Request::ReadDiscreteInputs(addr, cnt) => {
                let ctx = self.ctx.clone();
                let fut = async move {
                    let mut ctx = ctx.lock().await;
                    let rsp = ctx.read_discrete_inputs(addr, cnt).await.unwrap()?;
                    Ok(Some(Response::ReadDiscreteInputs(rsp)))
                };
                Box::pin(fut)
            }
            Request::WriteSingleCoil(addr, data) => {
                let ctx = self.ctx.clone();
                let fut = async move {
                    let mut ctx = ctx.lock().await;
                    ctx.write_single_coil(addr, data).await.unwrap()?;
                    Ok(Some(Response::WriteSingleCoil(addr, data)))
                };
                Box::pin(fut)
            }
            Request::WriteMultipleCoils(addr, datas) => {
                let datas = datas.into_owned();
                let ctx = self.ctx.clone();
                let fut = async move {
                    let mut ctx = ctx.lock().await;
                    ctx.write_multiple_coils(addr, &datas).await.unwrap()?;
                    Ok(Some(Response::WriteMultipleCoils(addr, datas.len() as u16)))
                };
                Box::pin(fut)
            }
            Request::WriteSingleRegister(addr, data) => {
                let ctx = self.ctx.clone();
                let fut = async move {
                    let mut ctx = ctx.lock().await;
                    ctx.write_single_register(addr, data).await.unwrap()?;
                    Ok(Some(Response::WriteSingleRegister(addr, data)))
                };
                Box::pin(fut)
            }
            Request::WriteMultipleRegisters(addr, datas) => {
                let datas = datas.into_owned();
                let ctx = self.ctx.clone();
                let fut = async move {
                    let mut ctx = ctx.lock().await;
                    ctx.write_multiple_registers(addr, &datas).await.unwrap()?;
                    Ok(Some(Response::WriteMultipleRegisters(addr, datas.len() as u16)))
                };
                Box::pin(fut)
            }
            Request::MaskWriteRegister(addr, and, or) => {
                let ctx = self.ctx.clone();
                let fut = async move {
                    let mut ctx = ctx.lock().await;
                    ctx.masked_write_register(addr, and, or).await.unwrap()?;
                    Ok(Some(Response::MaskWriteRegister(addr, and, or)))
                };
                Box::pin(fut)
            }
            Request::ReadWriteMultipleRegisters(rr, cnt, wr, datas) => {
                let datas = datas.into_owned();
                let ctx = self.ctx.clone();
                let fut = async move {
                    let mut ctx = ctx.lock().await;
                    let rsp = ctx.read_write_multiple_registers(rr, cnt, wr, &datas).await.unwrap()?;
                    Ok(Some(Response::ReadWriteMultipleRegisters(rsp)))
                };
                Box::pin(fut)
            }
            Request::ReportServerId => Box::pin(future::ready(Ok(Some(Response::ReportServerId(self.slave.into(), true, Vec::new()))))),
            Request::Custom(code, bytes) => {
                println!("unknown mb({}): {:02X?}", code, bytes);
                Box::pin(future::ready(Err(ExceptionCode::IllegalFunction)))
            }
        }
    }
}

#[tokio::main]
async fn main() {
    let lebai = lebai_sdk::connect("127.0.0.1".into(), true).await.unwrap();
    let mb_serial = lebai.get_item("plugin_modbus_rtu_slave_serial".into()).await.unwrap().value;
    let mb_baud_rate = lebai.get_item("plugin_modbus_rtu_slave_baud_rate".into()).await.unwrap().value;
    let mb_slave_id = lebai.get_item("plugin_modbus_rtu_slave_salve_id".into()).await.unwrap().value;
    let mb_simu = lebai.get_item("plugin_modbus_rtu_slave_simu".into()).await.unwrap().value;

    let socket_addr = if mb_simu == "true" {
        SocketAddrV4::new([127,0,0,1].into(), 3050)
    } else {
        SocketAddrV4::new([127,0,0,1].into(), 3051)
    };
    let client = tcp::connect(socket_addr.into()).await.unwrap();
    let slave = Slave(mb_slave_id.parse().unwrap_or(30));
    let service = Service {
        slave,
        ctx: Arc::new(Mutex::new(client)),
    };

    let serial = format!("/dev/ttyS{}",if mb_serial.is_empty(){"1"}else{&mb_serial});
    let server_builder = tokio_serial::new(serial, mb_baud_rate.parse().unwrap_or(115200));
    let server_serial = tokio_serial::SerialStream::open(&server_builder).unwrap();
    #[cfg(unix)]
    server_serial.set_exclusive(true)?;
    let server = Server::new(server_serial);

    if let Err(err) = server.serve_forever(service).await {
        eprintln!("{err}");
    }
}
